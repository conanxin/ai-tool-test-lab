# Anatomy × Evidence-first: B-tree 索引档案柜（P0 语义基线）

An interactive B-tree search and insertion explainer with inspectable **algorithmic invariants** and an explicit **evidence / model-assumption boundary**. A first open-source experiment for integrating [Anatomy](https://github.com/wheresryan22/anatomy) with explorable research media.

> **Scope matters:** This P0 uses an original lightweight SVG visualization, **not yet the Anatomy drawing kit**. Hermes's next task is to reproduce/upgrade the visual using the actual upstream Skill and its geometry checks. Do not mistake passing Node tests for a completed Anatomy audit.

## Try it

- [Open the interactive demo on GitHub Pages](https://conanxin.github.io/ai-tool-test-lab/cases/anatomy-evidence-btree-v0/)
- Search for `45` (present), `57` (absent), or insert a new integer.
- Use **← / →** to inspect each actual B-tree search event.
- Model: unique integer keys, minimum degree `t=2`, in-memory single-threaded B-tree; **not** an assertion about the internal index of BOOK-ID-SEARCH.

## Run tests (no installation or API key)

```bash
cd cases/anatomy-evidence-btree-v0
npm run check
```

The Node standard-library tests cover B-tree insertion/splitting/search correctness, search traces, duplicate behavior, invalid input, random deterministic regression, structural invariants, and source-claim validation. `scripts/audit.mjs` checks static accessibility/runtime prerequisites. A separate optional Playwright smoke test exercises the real browser interaction (it uses an inline same-source harness when local navigation is blocked). **Neither is an upstream Anatomy geometry audit.**

Optional browser interaction test when Python Playwright and Chromium are installed:

```bash
python tests/browser_smoke.py
```

To view the demo locally:

```bash
python3 -m http.server 8765
# open http://localhost:8765/   (run inside this case directory)
```

## Research structure

| Component | Purpose |
|---|---|
| `src/btree.mjs` | Reusable deterministic reference implementation; invariant validator and trace generator |
| `src/evidence.mjs` | Provenance register, evidence statuses and schema check |
| `index.html`, `src/app.mjs`, `src/styles.css` | Interactive SVG instrument, source and assumptions presented alongside |
| `tests/` | Standard-library regression tests |
| `scripts/audit.mjs` | Static UI and reference-model audit |
| `docs/HERMES_TASK.md` | Exact next-stage command/prompt for local Hermes |
| `docs/RESEARCH_NOTES.md` | Research findings and epistemic limitations |

## Sources

- [Ryan's Anatomy skill](https://github.com/wheresryan22/anatomy)
- [Anatomy design/verification notes](https://skills.wheresryan.sh/anatomy/how-i-built-it)
- [NIST B-tree definition](https://xlinux.nist.gov/dads/HTML/btree.html)
- [OpenDSA B-tree treatment](https://opendsa-server.cs.vt.edu/ODSA/Books/pubbook/odsa-all/fall-2019/Public_Instance/html/BTree.html)
- [Bret Victor, Explorable Explanations (2011 and 2024 note)](https://worrydream.com/ExplorableExplanations/)

## Stage receipt

- P0 semantic baseline: code authored; automated tests run locally by ChatGPT and results to be recorded in the PR.
- P1 Hermes / upstream Anatomy kit: **NOT EXECUTED by this commit**.
- Browser interaction and screenshots: **passed in an inline Playwright fixture**; full hosted-page navigation and upstream Anatomy motion/geometry review are **NOT EXECUTED**.
- Public production integration with BOOK-ID-SEARCH or Conan Xin AI Lab: **NOT EXECUTED**.

License: uses the parent repository's MIT license. This case is independent of the original Anatomy repo; upstream code has not been copied here.
