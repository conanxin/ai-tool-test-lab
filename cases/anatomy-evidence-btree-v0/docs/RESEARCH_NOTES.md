# Anatomy + Evidence-first: P0 source-oriented research notes

Date: 2026-10-12 · Study ID: ANATOMY_EXPLORABLE_RESEARCH_P2

## Claim hierarchy

1. **Source-backed domain claim**: B-tree is an ordered balanced multiway search tree; searching examines keys and descends through a child range. Evidence: NIST DADS / OpenDSA.
2. **Model implementation**: this repository's deterministic minimum-degree implementation with validator. Evidence: executable unit/property tests; not independent proof of correctness.
3. **Demonstration choice**: `t=2`, memory-only, unique integer keys, invented filing cabinet geometry. Status: `MODEL_ASSUMPTION` or `INTERPRETATION`, not hardware fact.
4. **Visual claim**: SVG nodes and connecting arms depict state computed by (2). Status: `IMPLEMENTED_STATIC`; browser and spatial/visual audits remain outstanding.
5. **Upstream Anatomy usage**: the same exercise should be built with upstream kit and verified with `audit/capture/drive/lines`. Status: `PENDING_HERMES`.

## Critical distinction

Anatomy can make the object itself an explanation; Bret Victor's stronger explorable argument requires inspectable facts, assumptions and computations, including the possibility of refutation. A beautiful diagram with a self-consistent model can still express a false physical or historical assertion.

## Domain adaptation guidance

For BOOK-ID-SEARCH, do not claim it uses the exact B-tree degree or algorithm above without examining the deployed database and query plan. For historical architecture, distinguish primary measurements, reconstruction assumptions and visualization metaphors. Generated geometry must never overwrite evidence.

## Test inventory and expansion

| Gate | P0 status | Next step |
|---|---|---|
| Reference B-tree structure | automated unit/property tests | Hermes cross-check against another implementation |
| Search trace | deterministic transition assertions | state-to-frame continuity test |
| Evidence mapping | source/status validation | claim/geometry mapping |
| Accessible UI | static HTML audit + local Playwright inline-harness smoke: desktop and 390px PASS | repeat on hosted page with network access |
| Geometry | not tested | upstream Anatomy kit `--audit` |
| Animation | step transitions only, Playwright step navigation PASS | Anatomy drive/contact sheet |
| Publication | GitHub PR public, when created | verify workflow and HTML URL |

## Reproducibility

No remote API, cloud training, secret, external runtime library or data from a user's personal books. Original upstream sources are linked in `README.md`. Use fixed command output and commit SHA in receipts; never claim a gate passed without an observed result.
