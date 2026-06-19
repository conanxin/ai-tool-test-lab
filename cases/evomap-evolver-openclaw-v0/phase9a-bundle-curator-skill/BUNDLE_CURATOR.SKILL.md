# BUNDLE_CURATOR.SKILL — Bundle Curator Skill (Phase 9A)

> Status: **DRAFT · human-reviewed · ATL-EVOMAP-9A**
> Generator: `scripts/evomap_curate_bundle.py` v0.1.0
> Base commit: `a56e756` (post-ATL-EVOMAP-8A nightly validation loop)
> Kit: OpenClaw / Hermes Local Evolution Kit
> Visibility: `private`

This document is the canonical operator-facing description of the
**Bundle Curator Skill** — a stdlib-only, offline-only meta-tool that
converts a hand-written *curator spec* into a draft *portable bundle*
ready for `evomap_inspect_bundle.py` → `evomap_validate_bundle.py` →
`evomap_apply_bundle.py --dry-run` → (optional) `evomap_apply_bundle.py --yes`
against an **isolated** target.

It is **not** an autonomous agent. It is a generator that hands drafts to
the existing tool chain and **stops there**. All decisions about
*whether* a bundle is real, whether to apply it to a real runtime, and
whether to publish anything remain with the human operator.

---

## 1. Purpose

Phase 9A ships a small, predictable tool that turns a JSON description
of "what kind of gene/capsule I want" into a portable bundle draft that
already satisfies:

- canonical bundle schema (`atl-evomap-portable-bundle-v0.1`)
- canonical import contract (matches the 4 existing canonical bundles)
- safety contract (no hub / no publish / no credits / private visibility
  / no approve / no solidify / no AI / no network / no real test runners
  / no real config mutation)
- denylisted signal-name + secret-pattern refusal at spec-time, so
  secrets never enter the bundle even by mistake

After generation, the existing tool chain is used unchanged. The
curator does **not** replace `evomap_inspect_bundle.py` /
`evomap_validate_bundle.py` / `evomap_apply_bundle.py`.

## 2. When to use

Use the curator when:

- You want to prototype a new portable bundle draft without writing
  bundle JSON by hand.
- You want the safety invariants enforced automatically so you cannot
  accidentally produce a public / hub-bound / credit-consuming draft.
- You want the resulting bundle to be immediately inspectable and
  validatable by the existing tool chain.
- You want to seed a Phase 9A-style "bundle-curator skill" workflow for
  future domains (browser-control, Codex-only, Hermes-only, etc.).

Do **not** use the curator when:

- You already have a hand-crafted bundle and just want to inspect /
  validate / apply it. Use the existing tools directly.
- You need AI-assisted synthesis of gene strategy text. The curator
  does **not** call AI APIs. It only reformats operator-supplied text.
- You need to apply a bundle to a real runtime without an explicit
  operator phase boundary. Apply to real runtimes requires an
  authorization phase; the curator only writes to `--out-dir`.

## 3. Inputs

Single CLI flag:

| Flag | Required | Meaning |
|--|--|--|
| `--spec` | yes | Path to the curator spec JSON (`atl-evomap-curator-spec-v0.1`) |
| `--out-dir` | yes | Output directory for the generated bundle / gene / capsule / README |
| `--bundle-name` | no | Override the bundle filename (default: derived from `gene.id`) |
| `--dry-run` | no | Print planned writes; do not touch the filesystem |
| `--strict` | no | Strict mode (exit 2 on validation failure; current behavior matches non-strict for all enforced rules) |

The curator reads **only** the single `--spec` file. It does **not**
recursively scan the repository, does **not** read `.env`, does **not**
read runtime files, and does **not** contact any network endpoint.

## 4. Outputs

In `--dry-run` mode:

- A single JSON result printed to stdout, summarizing planned writes,
  validation outcome, and safety contract. Filesystem is **not**
  modified.

In generation mode:

- `<out-dir>/<bundle-name>.bundle.json` — portable bundle JSON
  (`atl-evomap-portable-bundle-v0.1`).
- `<out-dir>/gene-<gene.id>.json` — standalone gene JSON.
- `<out-dir>/capsule-<capsule.id>.json` — standalone capsule JSON.
- `<out-dir>/README.generated.md` — operator-facing draft README that
  enumerates identity, signals, strategy, constraints, execution
  trace, safety block, kit provenance, and the required review
  checklist.

Plus a single JSON result printed to stdout describing what was
written.

## 5. Safety boundaries (hard-enforced)

The curator **always**:

- Runs an AST self-check at startup that fails if any non-stdlib
  import is present in its own source file. This is a defense-in-depth
  guard so the curator can never silently pick up a third-party
  dependency.
- Refuses any spec whose `bundle.visibility` or `capsule.visibility`
  is not `"private"`.
- Refuses any spec whose `safety` block does not contain exactly
  `hub="disabled"`, `publish="disabled"`, `credits=0`,
  `visibility="private"`.
- Refuses any spec whose `gene.signals_match` or `capsule.trigger`
  contains a denylisted signal-name token (case-insensitive substring
  match). The denylist is a strict superset of the Phase 7A apply-tool
  denylist and adds password/cookie/bearer/csrf/session-token/etc.
- Refuses any spec whose signal strings, constraint strings, or
  strategy strings contain secret-like patterns (OpenAI key shape,
  GitHub PAT shape, `Authorization: Bearer` header, JWT shape,
  `BEGIN PRIVATE KEY` block, 12+ digit pure-numeric token). Detected
  matches are **redacted** in the result JSON before being echoed back,
  so the curator never returns the secret-like substring to the caller.
- Hard-codes `visibility: "private"` in every generated artifact's
  provenance block; the spec cannot override this.
- Resolves every output path under `--out-dir` and refuses any path
  that escapes the out-dir. The default out-dir is **never** the repo
  root, never `.evolver/`, never `memory/`, never any tracked repo
  directory; the caller must pass an explicit out-dir.

The curator **never**:

- Calls the EvoMap Hub or sets `A2A_HUB_URL`.
- Runs `evolver run`, `evolver review`, `evolver review --approve`,
  `evolver solidify`, or `evolver --loop`.
- Auto-publishes any artifact.
- Consumes credits or triggers ATP autobuy.
- Calls OpenAI / Codex / GitHub Copilot / any AI API.
- Calls the Telegram API.
- Calls `curl` / `wget` / `httpx` / `requests` / `urllib` / any HTTP
  client. The `urllib` stdlib module is in the import denylist.
- Runs real test runners (`pytest`, `npm test`, `cargo test`,
  `go test`, `mvn test`).
- Reads `.env` file contents (the AST denylist + the single-file
  read scope combine to enforce this).
- Reads or writes real API keys, tokens, cookies, Authorization
  headers, private keys, or chat IDs.
- Modifies real OpenClaw / Hermes / systemd / cron configuration.
- Installs cron. Creates systemd timers.
- Modifies Evolver package source.
- Tracks `runtime/.evolver/` or `runtime/memory/` in the repository.

## 6. Curator spec schema

Schema version: `atl-evomap-curator-spec-v0.1`.

A reference example is at
`templates/curator-spec.schema.example.json`. The minimal required
top-level keys are:

| Key | Type | Required value |
|--|--|--|
| `schema_version` | string | `"atl-evomap-curator-spec-v0.1"` |
| `bundle.schema_version` | string | `"atl-evomap-portable-bundle-v0.1"` |
| `bundle.source_phase` | string | e.g. `"ATL-EVOMAP-9A"` |
| `bundle.target_gene_id` | string | must equal `gene.id` |
| `bundle.target_capsule_id` | string | must equal `capsule.id` |
| `bundle.visibility` | string | `"private"` (hard-required) |
| `gene.type` | string | `"Gene"` |
| `gene.id` | string | non-empty, matches `bundle.target_gene_id` |
| `gene.category` | string | e.g. `"repair"` / `"optimize"` |
| `gene.signals_match` | list[string] | non-empty, no denylisted tokens, no secret patterns |
| `gene.strategy` | list[string] | non-empty |
| `gene.summary` | string | non-empty |
| `capsule.schema_version` | string | `"1.6.0"` (Evolver capsule schema) |
| `capsule.type` | string | `"Capsule"` |
| `capsule.id` | string | non-empty, matches `bundle.target_capsule_id` |
| `capsule.gene` | string | must equal `gene.id` |
| `capsule.status` | string | e.g. `"success"` |
| `capsule.confidence` | number | `0 <= x <= 1` |
| `capsule.visibility` | string | `"private"` (hard-required) |
| `capsule.source` | string | provenance tag, e.g. `"bundle_curator_phase9a"` |
| `capsule.trigger` | list[string] | non-empty, no denylisted tokens |
| `capsule.execution_trace` | list[object] | **>= 3** steps, each with `stage` / `command` / `exit_code` / `result` |
| `safety.hub` | string | `"disabled"` |
| `safety.publish` | string | `"disabled"` |
| `safety.credits` | number | `0` |
| `safety.visibility` | string | `"private"` |

Plus `fixture_summary` (optional) describing whether the bundle is
sample / offline / no-secret.

## 7. Validation sequence

The curator runs these checks in order; first failure ends the run.

1. AST self-check on the curator source file. Fails → exit 2.
2. `--spec` is an existing file. Fails → exit 2.
3. `--spec` parses as JSON. Fails → exit 2.
4. Top-level `schema_version` matches. Fails → exit 1 (or 2 if `--strict`).
5. Bundle / gene / capsule / safety blocks each have required fields
   and types. Fails → exit 1.
6. ID consistency invariants
   (`gene.id == bundle.target_gene_id`,
    `capsule.id == bundle.target_capsule_id`,
    `capsule.gene == gene.id`).
   Fails → exit 1.
7. Capsule `execution_trace` has **>= 3** steps. Fails → exit 1.
8. Safety block has hard-required values
   (`hub=disabled`, `publish=disabled`, `credits=0`,
    `visibility=private`).
   Fails → exit 1.
9. Every signal in `gene.signals_match` and `capsule.trigger` is
   scanned for denylisted tokens and secret patterns. Hits cause
   refusal (exit 1). The result JSON returns the pattern name and a
   **redacted** snippet; the raw match is never echoed.
10. Constraint strings, strategy strings, summary strings are also
    secret-scanned. Hits cause refusal.

After all checks pass, the curator computes paths, ensures every path
is inside `--out-dir`, builds the bundle / gene / capsule / README
in-memory, and (in generation mode) writes them out.

## 8. Refusal conditions (summary)

The curator refuses the spec (does not write any file) when **any** of:

- AST self-check fails (curator source is not stdlib-only).
- Spec file is missing or unparseable JSON.
- Top-level `schema_version` is not `atl-evomap-curator-spec-v0.1`.
- Bundle / gene / capsule / safety blocks are missing required fields.
- ID consistency invariants fail (gene.id / capsule.id / capsule.gene
  cross-references).
- `bundle.visibility` or `capsule.visibility` is not `"private"`.
- `capsule.execution_trace` has fewer than 3 steps.
- `safety.hub / safety.publish / safety.credits / safety.visibility`
  do not match the hard-required values.
- Any signal name contains a denylisted token.
- Any signal / constraint / strategy / summary string contains a
  secret-like pattern.
- Resolved output path escapes `--out-dir`.

In all refusal cases, the curator returns a JSON result with
`ok=false` and a non-empty `errors` array. Exit code is `1` for normal
refusal, `2` for file / AST / strict-mode refusal.

## 9. Example command

Dry-run validation:

```bash
python3 scripts/evomap_curate_bundle.py \
    --spec cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/specs/sample-safe-bundle.curator-spec.json \
    --out-dir cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated \
    --dry-run
```

Generate:

```bash
python3 scripts/evomap_curate_bundle.py \
    --spec cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/specs/sample-safe-bundle.curator-spec.json \
    --out-dir cases/evomap-evolver-openclaw-v0/phase9a-bundle-curator-skill/generated \
    --bundle-name sample-safe-bundle.bundle.json \
    --strict
```

## 10. Expected result

For a valid spec, the result JSON contains:

```json
{
  "ok": true,
  "mode": "generated",
  "spec": "...",
  "out_dir": "...",
  "bundle_path": "...",
  "gene_path": "...",
  "capsule_path": "...",
  "readme_path": "...",
  "gene_id": "...",
  "capsule_id": "...",
  "signals_count": <int>,
  "execution_trace_steps": <int>,
  "secret_hits": [],
  "rejected_signals": [],
  "strict": true|false,
  "safety_summary": {
    "hub": "disabled",
    "publish": "disabled",
    "credits": 0,
    "approve": "not_executed",
    "solidify": "not_executed",
    "evolver_run": "not_executed",
    "evolver_review": "not_executed",
    "real_cron_install": "not_executed",
    "systemd_timer_install": "not_executed",
    "network_calls": "not_executed",
    "real_tests": "not_executed",
    "no_env_file_content_scanned": true,
    "stdlib_only": true,
    "visibility": "private"
  }
}
```

The generated bundle can then be fed to the existing tool chain:

```bash
python3 scripts/evomap_inspect_bundle.py  --bundle <bundle_path>
python3 scripts/evomap_validate_bundle.py --bundle <bundle_path>
python3 scripts/evomap_apply_bundle.py   --bundle <bundle_path> \
    --target-runtime /tmp/<isolated-target> \
    --inject-signals-from <bundle_path> \
    --dry-run
```

…and only after those three return `ok=true` should the operator
manually invoke `evomap_apply_bundle.py --yes` against the isolated
target.

## 11. What this skill does NOT do

- It does **not** call any AI to design strategy text. Strategy is
  operator-supplied and reformatted as-is.
- It does **not** auto-read real runtime state.
- It does **not** read `.env` files.
- It does **not** connect to any Hub.
- It does **not** publish anything.
- It does **not** approve or solidify.
- It does **not** install cron or create systemd timers.
- It does **not** run real test suites.
- It does **not** modify evolver source.
- It does **not** track `runtime/.evolver/` or `runtime/memory/` in
  git.

## 12. Integration with Phase 8A

The nightly validation loop runner (`scripts/evomap_nightly_validate.py`)
already validates the **4 canonical bundles** as part of its 9
blocking checks. Phase 9A adds the *generation* capability: once a
new curator-generated bundle is moved into a canonical position, the
nightly runner's manifest can be extended to include it in the bundle
inspect / validate cycle. That integration is explicitly out of scope
for Phase 9A and is left as a future operator-led step.

## 13. Future extensions (not in scope)

- **ATL-EVOMAP-9B** — Curator-to-nightly integration: extend the
  Phase 8A manifest to include curator-generated bundles in the
  nightly inspect / validate cycle.
- **ATL-EVOMAP-9C** — Domain-specific curator specs: ship curated
  specs for browser-control, Codex-test, and Hermes-systemd domains.
- **ATL-EVOMAP-9D** — Curator-driven apply-to-canary: a guarded
  workflow that, on operator approval, applies curator-generated
  bundles to a canary runtime and reports back.

These are documented as future possibilities; they are **not** part
of Phase 9A deliverables and require their own operator authorization
phases.