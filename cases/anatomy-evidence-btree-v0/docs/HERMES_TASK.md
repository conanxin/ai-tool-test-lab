# Local Hermes handoff — Anatomy source-first PoC P1

TASK_ID=CONANXIN_ANATOMY_HERMES_P1

Read this file as a task **after** opening the public GitHub case and the linked Notion research archive. Execute autonomously within the specified repo-scoped boundaries.

## Context / inputs

- Official skill: https://github.com/wheresryan22/anatomy
- Current baseline: https://github.com/conanxin/ai-tool-test-lab/tree/main/cases/anatomy-evidence-btree-v0 (if not on main yet, use active PR head)
- Notion: https://app.notion.com/p/3f734a28189a81699161dd858772aed5
- Reference implementation: `src/btree.mjs`; tests: `tests/btree.test.mjs` and `tests/evidence.test.mjs`.
- Work only in a clean independent clone/branch of `conanxin/ai-tool-test-lab`. Do not modify `books.conanxin.com`, `conanxin.github.io`, local Hermes configuration, other research repositories, Notion page history, or the upstream Anatomy repository.

## Goal

1. Read upstream Anatomy `SKILL.md`, appropriate references and `kit` examples; resolve/pin an actual upstream SHA.
2. Keep the audited B-tree reference model; implement a proper Anatomy-kit visual instrument with at least one intentional multi-part mechanical analogy, not merely decorated boxes.
3. Add real browser captures and native Anatomy geometry audit where supported. Avoid assuming any check ran unless it did; include output and screenshot filenames in the report.
4. Preserve SOURCE_BACKED versus MODEL_ASSUMPTION flags; make each UI readout use the actual tree state and trace.
5. Add tests for the rendered DOM and keyboard/search/insert states. Prefer small reproducible tests without new services.
6. Run all existing tests, collect an explicit PASS/FAIL/BLOCKED evidence table; open a public GitHub PR (no auto-merge if quality checks are pending). No changes outside this one case except a narrowly-scoped new workflow needed to test it.
7. Append a receipt to the existing Notion page if your Notion connection is available; otherwise write `docs/HERMES_RECEIPT.md` in the repo for later synchronization.

## Required closeout fields

```
TASK_ID
DEVICE_AND_HERMES_VERSION
UPSTREAM_ANATOMY_SHA
WORKTREE_PATH
BRANCH
CODE_SHA
TEST_COMMANDS_AND_COUNTS
GEOMETRY_AUDIT_STATUS
BROWSER_CAPTURE_STATUS
DEMO_URL
PR_URL
NOTION_WRITE_STATUS
BLOCKERS
NEXT_ACTION
```

Do not classify a preparation or start signal as task completion. If terminal/browser commands are blocked, record `BLOCKED`, the exact observed error and the next smallest repair. Do not reset/reconfigure Hermes or Desktop Commander as part of this task.
