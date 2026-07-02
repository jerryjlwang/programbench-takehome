# ProgramBench Take-Home

This repository contains two ProgramBench task recreations: one for an **existing** benchmark repo (`lua/lua`) and one for a **novel** repo (`ThakeeNathees/pocketlang`). A third task (`janet-lang/janet`) was built and hardened but set aside in favor of PocketLang; it is retained as a supporting record.

Each task follows the ProgramBench paper's construction pattern:

1. Pin a commit of an open-source program and build a gold executable.
2. Expose only the executable + usage docs to the solver (no source).
3. Harvest upstream tests and convert them to black-box behavioral pytest tests.
4. Measure line/branch coverage; add coverage-guided generated tests.
5. Run an assertion-quality gate (static linter + gold/dummy dynamic checks).
6. Run a mini-SWE agent (Gemini Flash) in a hardened cleanroom and evaluate its submission.

---

## Repository layout

```
programbench-takehome/
├── README.md                          ← this file
├── AGENTS.md                          ← repo-level description
├── programbench/                      ← cloned ProgramBench framework (upstream)
├── runs/                              ← raw artifact from the very first Lua agent run
│   └── lua_miniswe_20260629_225007/
└── tasks/
    ├── reproduced_lua/                ← TASK 1: existing repo (lua/lua)
    ├── reproduced_pocketlang/         ← TASK 2: novel repo (ThakeeNathees/pocketlang)
    └── reproduced_janet/              ← supporting record (janet-lang/janet, not final)
```

`runs/` at the root holds only the earliest Lua agent run (kept as a raw artifact). All subsequent eval outputs live under `tasks/<task>/reports/evals/`.

---

## Task 1 — Existing repo: `lua/lua`

**Directory:** `tasks/reproduced_lua/`

### What it is

A recreation of the existing ProgramBench catalog task `lua__lua.c6b4848`. The generated suite was expanded to exactly match the catalog's active test count (1,338).

### Key numbers

| Metric | Value |
|---|---|
| Pinned commit | `c6b484823806e08e1756b1a6066a3ace6f080fae` |
| Harvested tests | 18 passed |
| Generated tests | 1,338 passed |
| Harvested coverage | 94.3% line, 88.6% branch |
| Generated coverage | 95.6% line, 89.1% branch |
| Quality gate | 21 checks, 0 static findings; gold 1338/1338, dummy 0/1338 |
| Agent score (Gemini Flash, low reasoning) | **180 / 1,338** |

### Where to look

```
tasks/reproduced_lua/
├── task.yaml                                   ← repo, commit, gold hash
├── task_env/                                   ← what the solver sees (executable + docs)
├── tests_harvested/eval/tests/                 ← 18 black-box pytest tests
├── tests_generated/eval/tests/                 ← 1,338 generated behavioral tests
├── reports/
│   ├── pipeline_status.md                      ← full pipeline narrative
│   ├── coverage_harvested/coverage_summary.txt ← baseline coverage numbers
│   ├── coverage_generated/coverage_summary.txt ← post-iteration coverage numbers
│   ├── quality_generated/quality_report.json   ← linter + gold/dummy results
│   ├── qc/generated_qc_report.md               ← aggregated QC report
│   ├── qc/lm_as_judge_review.md                ← LM-as-judge fairness audit
│   ├── qc/deterministic_fairness_report.md     ← deterministic fairness checks
│   ├── fairness_lm_judge.md                    ← solver-facing fairness summary
│   └── evals/
│       ├── lua_miniswe_20260629_225007/         ← early run (7/1338)
│       │   └── summary.json
│       └── lua_miniswe_20260701_033746/         ← representative final run (180/1338)
│           ├── summary.json
│           └── submission_report.md
└── scripts/                                    ← build, coverage, eval, QC scripts
```

**Start here:** `reports/pipeline_status.md` — it documents every pipeline stage with repro commands.

**Agent run to look at:** `reports/evals/lua_miniswe_20260701_033746/` — this is the representative Gemini Flash run that compiled, passed the oracle-rejection guard, and scored 180/1,338.

---

## Task 2 — Novel repo: `ThakeeNathees/pocketlang`

**Directory:** `tasks/reproduced_pocketlang/`

### What it is

A novel ProgramBench task built from scratch for PocketLang, a small Python-inspired scripting language implemented in C. PocketLang does not exist in the ProgramBench catalog — the full pipeline (harvest, generate, QC, evaluate) was run from a clean start.

### Key numbers

| Metric | Value |
|---|---|
| Pinned commit | `cc73ca61b113d48ee130d837a7a8b145e41de5ce` |
| Harvested tests | 25 passed |
| Generated tests | 421 passed |
| Harvested coverage | 68.0% line, 59.6% branch |
| Generated coverage | 72.7% line, 62.3% branch |
| Quality gate | 21 checks, 0 static findings; gold 421/421, dummy 0/421 |
| Agent score (Gemini Flash) | **3 / 421** |

### Why the agent scored low

PocketLang's implementation surface (VM, compiler, closures, built-in types) requires rebuilding core language machinery that a lightweight Gemini Flash agent cannot derive from black-box observation alone. A score of 3/421 is expected — the same pattern holds for Janet and the weaker Lua runs.

### Where to look

```
tasks/reproduced_pocketlang/
├── task.yaml                                      ← repo, commit, gold hash
├── task_env/                                      ← what the solver sees (executable + docs)
├── tests_harvested/eval/tests/                    ← 25 black-box pytest tests
├── tests_generated/eval/tests/                    ← 421 generated behavioral tests
├── reports/
│   ├── pipeline_status.md                         ← full pipeline narrative
│   ├── coverage_harvested/coverage_summary.txt    ← baseline coverage
│   ├── coverage_generated/coverage_summary.txt    ← post-iteration coverage
│   ├── quality_generated/quality_report.json      ← linter + gold/dummy results
│   ├── qc/generated_qc_report.md                  ← aggregated QC report
│   ├── qc/lm_as_judge_review.md                   ← LM-as-judge fairness audit
│   ├── qc/deterministic_fairness_report.md        ← deterministic fairness checks
│   ├── fairness_lm_judge.md                       ← solver-facing fairness summary
│   └── evals/
│       ├── pocketlang_empty_stub/                 ← evaluator sanity check (0/421)
│       ├── pocketlang_bad_stub/                   ← evaluator sanity check (3/421 — only help/version)
│       └── pocketlang_miniswe_20260702_021259/    ← final agent run (3/421)
│           ├── summary.json
│           ├── submission_report.md
│           └── submission.tar.gz
└── scripts/                                       ← build, coverage, eval, QC scripts
```

**Start here:** `reports/pipeline_status.md` — documents every pipeline stage.

**Agent run to look at:** `reports/evals/pocketlang_miniswe_20260702_021259/` — the hardened Gemini Flash run, 3/421.

**Evaluator hardening:** The eval script includes guards for oracle-byte injection, subprocess delegation, substring command dispatch, and tainted-buffer dispatch — all patterns the agent attempted during Janet development. `reports/evals/pocketlang_empty_stub/` and `pocketlang_bad_stub/` show the 0/421 and 3/421 sanity baselines.

---

## Supporting record — `janet-lang/janet`

**Directory:** `tasks/reproduced_janet/`

Janet was the first novel-repo attempt. The full pipeline was completed — gold build, harvested/generated tests, QC, fairness, 11 mini-SWE runs — but the agent consistently scored 0–1/381 even after extensive scaffold hardening. The task was set aside in favor of PocketLang, which has a smaller implementation surface.

Janet is retained here because it documents the scaffold hardening work (oracle-byte rejection, wrapper detection, subprocess/dispatch gates) that carried over into the PocketLang evaluator.

### Key numbers

| Metric | Value |
|---|---|
| Pinned tag | v1.41.2 (`0fea20c82182fe661f75b00a8889d801fe2d79b6`) |
| Generated tests | 381 passed |
| Generated coverage | 75.3% line, 68.5% branch |
| Agent best score across 11 runs | **1 / 381** |

### Where to look

```
tasks/reproduced_janet/
├── reports/
│   ├── pipeline_status.md             ← full pipeline narrative
│   ├── solve_attempts_summary.md      ← table of all 11 agent runs with outcomes
│   ├── qc/generated_qc_report.md      ← aggregated QC report
│   ├── qc/lm_as_judge_review.md       ← LM-as-judge fairness audit
│   └── evals/                         ← 11 run directories, each with summary.json
└── scripts/
```

**Start here:** `reports/solve_attempts_summary.md` — explains why each of the 11 runs failed and what evaluator hardening was added in response.

---

## Programbench framework

**Directory:** `programbench/`

This is the cloned ProgramBench framework used for reference. It contains the catalog task data for Lua at `programbench/src/programbench/data/tasks/lua__lua.c6b4848/` (1,387 listed / 1,338 active tests), which was used to align the generated Lua suite count.

---

## Quickstart repro commands

All commands run from the repo root. Docker is required.

```bash
# Validate generated Lua tests against gold
docker run --rm --platform linux/amd64 \
  -v "$PWD/tasks/reproduced_lua/task_env/executable:/workspace/executable:ro" \
  -v "$PWD/tasks/reproduced_lua/tests_generated/eval:/workspace/eval:ro" \
  python:3.11-slim bash -lc \
  "pip install pytest -q 2>/dev/null && cd /workspace && python3 -m pytest eval/tests -v --tb=short"

# Validate generated PocketLang tests against gold
docker run --rm --platform linux/amd64 \
  -v "$PWD/tasks/reproduced_pocketlang/task_env/executable:/workspace/executable:ro" \
  -v "$PWD/tasks/reproduced_pocketlang/tests_generated/eval:/workspace/eval:ro" \
  python:3.11-slim bash -lc \
  "pip install pytest -q 2>/dev/null && cd /workspace && python3 -m pytest eval/tests -v --tb=short"

# Evaluate a submission (PocketLang example)
bash tasks/reproduced_pocketlang/scripts/evaluate_submission.sh \
  tasks/reproduced_pocketlang/reports/evals/pocketlang_miniswe_20260702_021259
```
