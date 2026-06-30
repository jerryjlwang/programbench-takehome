# AGENTS.md

This repository is focused on a fresh ProgramBench task-recreation pipeline for
`lua/lua`.

## What this repository is

A ProgramBench take-home implementation that reconstructs an existing benchmark
task from scratch, following the ProgramBench paper's task-construction method:
build a pinned gold executable, expose only executable behavior to solvers,
harvest upstream tests into black-box behavioral tests, then use
coverage-guided iterations plus assertion-quality checks to add or revise tests
until coverage and suite quality are satisfactory.

## Current task: lua/lua

- Repository: `https://github.com/lua/lua`
- ProgramBench catalog task: `lua__lua.c6b4848`
- Pinned commit: `c6b484823806e08e1756b1a6066a3ace6f080fae`
- Language: C
- Difficulty: medium
- Gold binary SHA256:
  `56c87d948e1fa58d5854c40259e15dc974997fdd8515e2353e37a95ef404926a`
- ProgramBench catalog tests: 1,387 listed, 49 ignored, 1,338 active

## Directory structure

```text
programbench/                    # Cloned ProgramBench framework
tasks/
  reproduced_lua/
    _src/lua/                    # Pinned lua/lua clone for build/coverage only
    gold/lua                     # Gold executable
    task_env/                    # Solver-facing environment
      executable                 # Gold binary oracle for solver observation
      docs/                      # USAGE.md, help.txt
      compile.sh                 # Solver build template
    tests_harvested/             # Behavioral tests harvested from upstream testes/
      eval/
        fixtures/testes/         # Upstream Lua test inputs
        tests/                   # Pytest wrappers over executable behavior
        run.sh
      build.sh
    tests_generated/             # Harvested tests plus coverage-guided additions
      eval/
        cases/generated_cases.json
        fixtures/testes/
        tests/
        run.sh
      build.sh
    scripts/
      build_gold.sh
      coverage_harvested.sh
      coverage_generated.sh
      build_qc_report.py
      generate_large_cases.py
      quality_generated.sh
      quality_gate.py
    logs/
    reports/
      pipeline_status.md
      coverage_harvested/
      coverage_generated/
      quality_generated/
      qc/
```

## Key commands

### Build gold executable

```bash
bash tasks/reproduced_lua/scripts/build_gold.sh
```

### Validate harvested tests against gold

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD/tasks/reproduced_lua/task_env/executable:/workspace/executable:ro" \
  -v "$PWD/tasks/reproduced_lua/tests_harvested/eval:/workspace/eval:ro" \
  python:3.11-slim bash -lc "
    pip install pytest -q 2>/dev/null
    cd /workspace && python3 -m pytest eval/tests -v --tb=short
  "
```

### Validate generated tests against gold

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD/tasks/reproduced_lua/task_env/executable:/workspace/executable:ro" \
  -v "$PWD/tasks/reproduced_lua/tests_generated/eval:/workspace/eval:ro" \
  python:3.11-slim bash -lc "
    pip install pytest -q 2>/dev/null
    cd /workspace && python3 -m pytest eval/tests -v --tb=short
  "
```

### Measure coverage

```bash
bash tasks/reproduced_lua/scripts/coverage_harvested.sh
bash tasks/reproduced_lua/scripts/coverage_generated.sh
```

### Run assertion-quality gate

```bash
bash tasks/reproduced_lua/scripts/quality_generated.sh
```

### Rebuild downstream QC report

```bash
python3 tasks/reproduced_lua/scripts/build_qc_report.py
```

### Run mini-SWE-agent solve scaffold on Lua

```bash
export GEMINI_API_KEY=...  # or GOOGLE_API_KEY / GOOGLE_GENERATIVE_AI_API_KEY
MODEL=gemini/gemini-3.5-flash \
  bash tasks/reproduced_lua/scripts/run_miniswe_lua.sh
```

This builds a local `programbench-lua-cleanroom:local` Docker image from
`task_env/`, runs the mini-SWE ProgramBench scaffold with `--network none`
inside the solver container, and writes:

```text
runs/<run-name>/lua__lua.c6b4848/submission.tar.gz
runs/<run-name>/lua__lua.c6b4848/lua__lua.c6b4848.traj.json
```

### Evaluate a produced submission with generated tests

```bash
bash tasks/reproduced_lua/scripts/evaluate_submission.sh runs/<run-name>
```

This compiles the submitted code with network disabled, rejects candidates
whose executable hash matches the gold oracle, and runs the 1,338 generated
behavioral tests. Results are written under
`tasks/reproduced_lua/reports/evals/<run-name>/`.

## Current results

- Harvested suite: 18 tests passed
- Generated suite: 1,338 tests passed, matching the ProgramBench active-test
  count for `lua__lua.c6b4848`
- Harvested coverage: 94.3% line, 88.6% branch
- Generated coverage: 95.6% line, 89.1% branch
- Quality gate: gold run passes all 1,338 tests; dummy executable passes 0;
  screenshot-rule assertion linter has 21 checks and 0 static findings
- Downstream QC report:
  `tasks/reproduced_lua/reports/qc/generated_qc_report.json`

## Notes

- Fairness/non-leakage audit report:
  `tasks/reproduced_lua/reports/fairness_lm_judge.md`
- Keep solver-facing `task_env/` limited to executable, usage docs, and build
  template. Do not place source, upstream tests, coverage reports, or generated
  tests there.
