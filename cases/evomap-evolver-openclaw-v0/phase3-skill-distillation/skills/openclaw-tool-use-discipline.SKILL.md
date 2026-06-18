# OpenClaw Tool Use Discipline Skill

> Domain-specific skill for the ai-tool-test-lab repository.
> Target: Phase 3a of ATL-EVOMAP-3A EvoMap Evolver skill distillation.
> Designed to be ingested by `evolver distill` to produce an OpenClaw-specific Gene.

---

## 1. Purpose

This skill solves a recurring pattern observed in OpenClaw sessions within
`ai-tool-test-lab` (and similar agentic codebases):

> **Tool Bypass / Over-Use of `exec`**
>
> During long multi-step agent loops, the assistant sometimes uses `exec` to run
> `cat`, `grep`, `sed -i`, `head`, `tail`, `jq`, or `ls` for tasks that are
> already covered by first-class tools (`read`, `search`, `edit`, `process`).
> This produces:
>
> - non-idempotent side effects (e.g. accidental file mutation via `sed -i`),
> - invisible reasoning (the search hits never enter the conversation as
>   structured `read` results),
> - poor replayability (a future `evolver run` cannot observe the assistant's
>   intent because it lives in a transient bash invocation),
> - drift signals such as `tool_bypass:exec-on-grep` and
>   `protocol_drift:wrong-tool-for-file-read`.

The goal of this skill is to make the OpenClaw agent's tool usage
**disciplined, reviewable, and evolver-friendly** so that later phases
(3b signal detector, 3c solidify) can match it back to OpenClaw-specific Genes.

---

## 2. Trigger Signals

A session is a candidate for this skill when **any** of the following signals
are observed in the recent tool-call history or in the assembled
`memory_graph.jsonl` events:

| signal key                              | meaning                                                                 |
|----------------------------------------|-------------------------------------------------------------------------|
| `tool_bypass:exec-on-grep`             | `exec` was used to run `grep` / `rg` / `find` for content that could have been read with the `search` tool or an explicit `read`. |
| `repeated_tool_usage:exec`             | more than N `exec` calls per 10 tool calls in the same task without an explicit reason. |
| `protocol_drift:wrong-tool-for-file-read` | file content fetched through `exec cat` / `exec head` / `exec sed` instead of the `read` tool. |
| `session_context:openclaw`             | the session is identified as OpenClaw main or a child session.          |
| `repo_context:ai-tool-test-lab`        | the working directory is inside the `ai-tool-test-lab` repo.            |
| `mutation_risk:file-content`           | a non-idempotent `sed -i` / `awk -i` / `tee` was used in place of `edit`. |
| `evidence:no_read_for_file_path`       | the assistant has not called `read <path>` before referencing the contents of `<path>`. |

These signals are intentionally coarse — a future Phase 3b signal detector
will refine them. The point here is to give `evolver distill` a structured
label set so the distilled Gene has a stable `signals_match` array.

---

## 3. Strategy

When the above signals fire, apply the following discipline in this exact
order. The discipline is the **strategy** the distilled Gene will encode.

### 3.1 Read priority

1. **For any file whose contents the agent needs to reason about**:
   use the `read` tool. Never use `exec cat`, `exec head`, `exec tail`,
   `exec less`, or `exec sed -n 'p'` for that purpose.

2. **For repo-wide content search** (looking for a string across many files):
   use the `search` tool or `rg` via `exec` *only if* the `search` tool
   is unavailable. Always state the reason before invoking `exec`.

3. **For shell output that is genuinely ephemeral** (`npm test`,
   `git status`, `python3 scripts/validate_*.py`, `git push` output):
   `exec` is the right tool. Do not try to "edit" or "read" those.

### 3.2 Edit priority

4. **For any in-place file change**:
   use the `edit` tool with a precise `oldText` / `newText` patch. Never
   use `sed -i`, `awk -i inplace`, or `python -c "open(...).write(...)"`.
   Reason: `edit` is auditable, diff-friendly, and lets the
   `evolver review` step show the candidate diff cleanly.

5. **For any new file**:
   use `write`. Never `cat > file <<EOF` or `tee file`.

### 3.3 Justification rule

6. **Before any `exec` that is not a validator / build / git / package
   manager invocation**, the assistant must include a one-line
   `EXEC: <reason>` in its reasoning block. This is so that
   `evolver review` and human auditors can later see *why* an `exec`
   was chosen over a first-class tool.

### 3.4 Read-before-reference rule

7. **Never reference file contents in reasoning or output** unless a
   `read` of that file (or an explicit `search` hit list) appears in
   the same turn or in a quoted prior turn. This is what produces the
   `evidence:no_read_for_file_path` signal and is the single biggest
   source of hallucinated quotes in long sessions.

---

## 4. Constraints

The discipline is bounded by the same hard boundaries the user keeps for
the OpenClaw / Hermes / Codex stack. The distilled Gene must not relax
any of these:

- **No secrets** — never read, write, or print API keys, tokens, cookies,
  `Authorization` headers, `private_key`, `.env` files, or `*.pem` /
  `*.key` / `*.p12` contents.
- **No `.env` scan** — `grep .env` is forbidden; the only allowed
  reference is the literal string `.env` in `.gitignore` documentation.
- **No runtime state commit** — `.evolver/` and `memory/` directories
  at the repo root are runtime state and must remain in `.gitignore`.
  Fixture copies inside `cases/*/fixtures/*/.evolver/` are committed
  test artifacts and *are* allowed.
- **No real service mutation** — never edit
  `~/.openclaw/`, `~/.hermes/`, `systemd --user` units, or cron
  entries from a session that has absorbed this skill. The discipline
  applies only to the project the agent is currently working in.
- **No Hub connection** — `A2A_HUB_URL` must remain unset.
- **No publish** — `EVOLVER_AUTO_PUBLISH=false` is a hard prerequisite.
- **No `--loop` / no validator** — this skill is a *discipline*, not a
  background runner.
- **No credits / no ATP autobuy** — `EVOLVER_ATP_AUTOBUY=off` is a hard
  prerequisite.

---

## 5. Validation

After a session that has been run under this discipline, a human or a
follow-up `evolver run` should be able to verify all of the following
**PASS** conditions:

1. **Tool audit** — review the last 20 tool calls in the session
   transcript. Count `exec` invocations. The ratio of `exec` to
   `read+search+edit+write` should be ≤ 0.5 for any task that touches
   more than three files.

2. **Bypass detection** — search the transcript for the strings
   `exec cat`, `exec head`, `exec sed -i`, `exec awk`, `exec tee `,
   `cat > `. Any hit is a **FAIL** for this discipline.

3. **Edit pattern** — for any `git diff` produced during the task, the
   hunks should look like `edit` patches (small `oldText`/`newText`
   windows), not like full-file rewrites.

4. **Git hygiene** — `git status --short` should list only the expected
   case files, the validator script, the case README, and the case
   `data/cases.json` entry. There should be no `.evolver/`, no
   `memory/`, no `node_modules/`, no `.env` lines.

5. **Validator pass** — `python3 scripts/validate_evomap_phase3a_skill_distillation.py`
   must exit 0.

6. **Hard-boundary scan** — re-run the secret-pattern scan from the
   Phase 1/2/3a validators. Any hit is a **FAIL** regardless of the
   discipline score.

---

## 6. Expected Outcome

When this skill is distilled into a Gene and absorbed by `evolver run`,
the following outcomes are expected:

- **Reduced bypass** — the number of `tool_bypass:exec-on-grep` events
  in the `memory_graph.jsonl` for an OpenClaw session should drop
  noticeably over the first 3–5 evolver cycles in a new repo.

- **Better explainability** — `evolver review` will now see structured
  `read` results instead of one-shot bash transcripts, so the candidate
  diff it suggests will be more precise.

- **Gene signal match** — because this skill defines explicit
  `signals_match` entries (`tool_bypass:exec-on-grep`, `session_context:openclaw`,
  `repo_context:ai-tool-test-lab`), a future Phase 3c solidify can
  match it back to a session without falling through to
  `distilled_fallback` (which is what happened in Phase 2 when
  `gene_distilled_s2g-env-vars` was selected).

- **Phase 3b foundation** — the trigger signals above are exactly what
  a Phase 3b OpenClaw-specific signal detector will need to surface.
  This skill is therefore a prerequisite for the detector, not a
  parallel artifact.

---

## 7. Metadata

```yaml
skill_id: openclaw-tool-use-discipline
version: 0.1.0
phase: ATL-EVOMAP-3A
distill_target: evolver distill
session_context: openclaw
repo_context: ai-tool-test-lab
requires_hub: false
publishes_asset: false
consumes_credits: false
compatible_with_local_mode: true
```

---

*This skill is intentionally written in the EvoMap-style Skill schema
(see `genes.seed.json` and the `distill_fallback` selector). It is
designed to be the input to `evolver distill`, not a Gene yet.*
