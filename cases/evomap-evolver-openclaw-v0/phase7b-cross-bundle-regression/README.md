# ATL-EVOMAP-7B · Cross-Bundle Regression

**Status:** PASS (all 5 score dimensions)
**Date:** 2026-06-19
**Base:** 3112f07 (ATL-EVOMAP-7A)
**Target:** `/tmp/atl-evomap-7b-cross-bundle-target`

## Goal

Verify that all 3 canonical portable bundles (OpenClaw tool-use
discipline, Hermes systemd service recovery, Telegram message router
failure) can coexist in a single fresh isolated target runtime.

## Layout

```
phase7b-cross-bundle-regression/
├── README.md                                                       (this file)
├── ATL_EVOMAP_7B_CROSS_BUNDLE_REGRESSION_REPORT.md                 (full report)
└── artifacts/
    ├── apply-openclaw-dry-run-output.json
    ├── apply-openclaw-yes-output.json
    ├── apply-hermes-dry-run-output.json
    ├── apply-hermes-yes-output.json
    ├── apply-telegram-dry-run-output.json
    ├── apply-telegram-yes-output.json
    ├── cross-bundle-target-summary.json               (pre-smoke analyzer output)
    ├── cross-bundle-target-files.txt                  (file listing)
    ├── cross-bundle-signal-list.json                  (memory graph signal list)
    ├── evolver-run-cross-bundle-output.txt            (combined smoke run)
    ├── evolver-review-cross-bundle-output.txt         (combined smoke review)
    ├── cross-bundle-post-smoke-summary.json           (post-smoke analyzer output)
    ├── cross-bundle-grep.txt                          (grep result for required IDs/safety markers)
    ├── evolver-run-probe-openclaw-output.txt          (probe matrix: openclaw)
    ├── evolver-review-probe-openclaw-output.txt
    ├── evolver-run-probe-hermes-output.txt            (probe matrix: hermes)
    ├── evolver-review-probe-hermes-output.txt
    ├── evolver-run-probe-telegram-output.txt          (probe matrix: telegram)
    ├── evolver-review-probe-telegram-output.txt
    └── cross-bundle-regression-summary.json           (master regression summary)
```

## New tools

- `scripts/evomap_cross_bundle_analyze.py` — cross-bundle regression
  analyzer (Python stdlib only, `--target-runtime` only, reads only the
  6 fixed files written by the apply tool + evolver).

## New validator

- `scripts/validate_evomap_phase7b_cross_bundle_regression.py` —
  27 checks: 6 apply outputs, 2 analyzer outputs, 1 summary, 2 evolver
  outputs, 6 probe outputs, 1 main case README, 1 cases.json, 1
  cross-bundle report, 1 top-level report, 1 secret scan, 1 git
  status, 4 backward-compat validators (Phase 5/6A/6B/7A).

## Self-test results

| Score | Dimension | Result |
|--|--|--|
| A | Apply compatibility (3/3 dry-run + --yes PASS) | PASS |
| B | ID compatibility (3/3 genes, 3/3 capsules, 0 dups) | PASS |
| C | Signal compatibility (19/19 required, 0 dangerous, 0 pollution) | PASS |
| D | Combined evolver smoke (no crash, no Hub, score_ranked) | PASS |
| E | Safety (no Hub, no publish, no credits, no approve, no solidify) | PASS |

**Overall: PASS**

Selector probe matrix: 1/3 exact match (openclaw → openclaw), 2/3 PARTIAL
(hermes/telegram → openclaw picked by score_ranked because real session
context matched OpenClaw first). PARTIAL is acceptable per spec.

## Safety boundaries (20 preserved)

No Hub / no A2A_HUB_URL / no --loop / no validator / no auto-publish /
no credits / no ATP autobuy / no real Telegram creds / no .env scan /
no curl/wget/HTTP / no Telegram API / no real sendMessage / no real
config mutation / no Evolver source modification / no evolver
--approve / no solidify / no commit of runtime originals / Python
stdlib only / target under /tmp / only commit tools + artifacts +
reports + validator + README + data updates.

## Reproduce

```bash
cd /mnt/d/AI/ai-tool-test-lab

# 1. reset target with stub memory log
rm -rf /tmp/atl-evomap-7b-cross-bundle-target
mkdir -p /tmp/atl-evomap-7b-cross-bundle-target/memory
cd /tmp/atl-evomap-7b-cross-bundle-target
git init -q .
git config user.email "atl-local@example.invalid"
git config user.name "ATL Local"
echo "# ATL EvoMap 7B Cross-Bundle Target" > README.md
echo "# memory log $(date -u +%Y-%m-%d)" > memory/2026-06-18.md
git add README.md memory/
git commit -q -m "init cross-bundle target"
cd /mnt/d/AI/ai-tool-test-lab

# 2. apply 3 bundles (each: dry-run + --yes, with --inject-signals-from)
for spec in \
  "phase5-local-evolution-kit/bundle/openclaw-tool-use-discipline.bundle.json openclaw" \
  "phase6a-hermes-systemd-bundle/bundle/hermes-systemd-service-recovery.bundle.json hermes" \
  "phase6b-telegram-router-bundle/bundle/telegram-message-router-failure.bundle.json telegram"; do
    bundle=$(echo $spec | cut -d' ' -f1)
    name=$(echo $spec | cut -d' ' -f2)
    bundle_path="cases/evomap-evolver-openclaw-v0/$bundle"
    python3 scripts/evomap_apply_bundle.py \
        --bundle "$bundle_path" \
        --inject-signals-from "$bundle_path" \
        --target-runtime /tmp/atl-evomap-7b-cross-bundle-target --dry-run \
        > cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression/artifacts/apply-$name-dry-run-output.json
    python3 scripts/evomap_apply_bundle.py \
        --bundle "$bundle_path" \
        --inject-signals-from "$bundle_path" \
        --target-runtime /tmp/atl-evomap-7b-cross-bundle-target --yes \
        > cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression/artifacts/apply-$name-yes-output.json
done

# 3. analyze
python3 scripts/evomap_cross_bundle_analyze.py \
  --target-runtime /tmp/atl-evomap-7b-cross-bundle-target \
  > cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression/artifacts/cross-bundle-target-summary.json

# 4. combined evolver smoke
cd /tmp/atl-evomap-7b-cross-bundle-target
git add . && git commit -q -m "apply three EvoMap bundles for ATL-EVOMAP-7B"
unset A2A_HUB_URL
export EVOLVE_STRATEGY=repair-only
export EVOLVER_AUTO_PUBLISH=false
export EVOLVER_VALIDATOR_ENABLED=false
export EVOLVER_ATP_AUTOBUY=off
export EVOLVER_DEFAULT_VISIBILITY=private
evolver run 2>&1 > /mnt/d/AI/ai-tool-test-lab/cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression/artifacts/evolver-run-cross-bundle-output.txt
evolver review 2>&1 > /mnt/d/AI/ai-tool-test-lab/cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression/artifacts/evolver-review-cross-bundle-output.txt
cd /mnt/d/AI/ai-tool-test-lab

# 5. post-smoke analyze
python3 scripts/evomap_cross_bundle_analyze.py \
  --target-runtime /tmp/atl-evomap-7b-cross-bundle-target \
  > cases/evomap-evolver-openclaw-v0/phase7b-cross-bundle-regression/artifacts/cross-bundle-post-smoke-summary.json
```

## Validator

```bash
python3 scripts/validate_evomap_phase7b_cross_bundle_regression.py
```

Expected: `ALL CHECKS PASSED` / `Status: cross-bundle regression completed (PASS)`.
