# Lua ProgramBench Recreation Pipeline Status

## Task metadata

- Repository: `lua/lua`
- Pinned commit: `c6b484823806e08e1756b1a6066a3ace6f080fae`
- ProgramBench catalog task: `lua__lua.c6b4848`
- Language: C
- Difficulty: medium
- Gold executable SHA256: `56c87d948e1fa58d5854c40259e15dc974997fdd8515e2353e37a95ef404926a`

## ProgramBench paper alignment

This task recreation follows the ProgramBench construction pattern from the
paper: build a pinned open-source program into an executable oracle, expose only
the executable plus usage documentation to solvers, convert existing tests into
black-box behavioral tests, validate them against the gold executable, run an
assertion-quality gate, revise flagged tests, then iteratively add tests guided
by source line coverage of the gold implementation.

The fairness/non-leakage audit is intentionally left for the next pass, per the
current request.

## ProgramBench catalog target

Catalog file: `programbench/src/programbench/data/tasks/lua__lua.c6b4848/tests.json`

- Branches: 11
- Listed tests: 1,387
- Ignored tests: 49
- Active tests: 1,338

The generated suite has been expanded to exactly 1,338 collected tests, matching
the active ProgramBench catalog count for Lua.

## Built artifacts

- Gold source clone: `tasks/reproduced_lua/_src/lua`
- Gold executable: `tasks/reproduced_lua/gold/lua`
- Solver-facing executable: `tasks/reproduced_lua/task_env/executable`
- Solver-facing docs: `tasks/reproduced_lua/task_env/docs/`
- Build script: `tasks/reproduced_lua/scripts/build_gold.sh`
- Metadata: `tasks/reproduced_lua/task.yaml`

Gold build command:

```bash
bash tasks/reproduced_lua/scripts/build_gold.sh
```

## Harvested tests

Harvest source: upstream `testes/` directory from the pinned Lua repository.

Conversion decisions:

- Copied upstream Lua test fixtures into `tests_harvested/eval/fixtures/testes`.
- Used upstream `all.lua` in `_U=true` user-test mode to disable internal `T`
  hooks, long tests, and nonportable shell sections while preserving behavioral
  interpreter checks.
- Converted stable parts of `testes/main.lua` into pytest black-box tests for
  CLI options, stdin handling, BOM parsing, `LUA_INIT`, environment path
  priority, `-l`, warnings, `arg`, and invalid option handling.
- Assertions are over stdout, stderr, exit status, and filesystem-visible
  effects only.

Validation:

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD/tasks/reproduced_lua/task_env/executable:/workspace/executable:ro" \
  -v "$PWD/tasks/reproduced_lua/tests_harvested/eval:/workspace/eval:ro" \
  python:3.11-slim bash -lc \
  "pip install pytest -q 2>/dev/null && cd /workspace && python3 -m pytest eval/tests -v --tb=short"
```

Result: 18 passed.

## Coverage-guided generated tests

Generated branch: `tasks/reproduced_lua/tests_generated`

Strategy:

- Start from the harvested behavioral tests.
- Measure gold line coverage with GCC/gcovr.
- Target the largest black-box-accessible gaps, especially `lua.c` interactive
  and error-reporting paths plus `loadlib.c`/package searcher paths.
- Generate small, granular gold-captured Lua CLI cases instead of allowing one
  broad test to stand in for hundreds of behaviors.
- Keep generated cases executable-facing; no direct calls into C internals.

Added coverage-guided modules:

- `test_coverage_guided_cli.py`
- `test_coverage_guided_package.py`
- `test_generated_cases.py`
- `cases/generated_cases.json` with 1,306 gold-captured cases

Validation result: 1,338 passed.

Collection check:

```bash
docker run --rm --platform linux/amd64 \
  -v "$PWD/tasks/reproduced_lua/task_env/executable:/workspace/executable:ro" \
  -v "$PWD/tasks/reproduced_lua/tests_generated/eval:/workspace/eval:ro" \
  python:3.11-slim bash -lc \
  "pip install pytest -q 2>/dev/null && cd /workspace && python3 -m pytest eval/tests --collect-only -q"
```

Result: 1,338 tests collected.

## Assertion-quality gate

Quality gate scripts:

- `tasks/reproduced_lua/scripts/quality_gate.py`
- `tasks/reproduced_lua/scripts/quality_generated.sh`
- `tasks/reproduced_lua/scripts/build_qc_report.py`

Checks:

- Static AST assertion linter implementing the screenshot rule table:
  `no_assertions`, `trivially_true`, `sole_returncode`,
  `returncode_in_list`, `pass_body`, `assertion_disjunction`, `if_no_else`,
  `if_else_both_assert`, `try_except_swallow`, `all_assertions_weak`,
  `short_substring`, `golden_written_in_test`, `golden_no_equality`,
  `golden_docstring`, `for_no_guard`, `weak_sole_assertion`,
  `relative_length_assertion`, `any_all_no_guard`, `file_exists_no_content`,
  `only_negative_assertions`, and `catches`.
- Full pytest run against the gold executable.
- Full pytest run against a dummy executable that exits successfully with no
  output; no generated tests are allowed to pass this dummy.

The screenshot-rule pass flagged five blocking `short_substring` findings plus
low-severity missing `CATCHES` docstrings. Those tests were revised to use exact
or structural stdout/stderr assertions, parametrized short-message checks were
removed, and every generated test function now has a `CATCHES:` docstring.

Final result:

- Static rule catalog: 21 checks
- Static findings: 0
- Blocking static findings: 0
- Gold run: 1,338 passed, 0 failed
- Dummy run: 0 passed, 1,338 failed

Report: `tasks/reproduced_lua/reports/quality_generated/quality_report.json`

Downstream QC reports:

- `tasks/reproduced_lua/reports/qc/generated_qc_report.json`
- `tasks/reproduced_lua/reports/qc/generated_qc_report.md`

These reports aggregate the linter check catalog, every linter finding, gold and
dummy validation results, coverage line checks, per-file line coverage, and
paths to the raw quality/coverage artifacts.

Logging behavior:

- `logs/quality_generated.log` mirrors the full quality-gate JSON, including the
  linter check catalog and all findings.
- `logs/coverage_harvested.log` and `logs/coverage_generated.log` include the
  gcovr line-coverage tables in addition to the JSON/HTML coverage artifacts.

## Coverage results

Harvested baseline:

- Line coverage: 94.3% (`11107/11774`)
- Branch coverage: 88.6% (`5666/6394`)
- Report: `tasks/reproduced_lua/reports/coverage_harvested/coverage_summary.txt`

Generated iteration 1 plus count-matched expansion:

- Line coverage: 95.6% (`11259/11779`)
- Branch coverage: 89.1% (`5735/6435`)
- Report: `tasks/reproduced_lua/reports/coverage_generated/coverage_summary.txt`

Notable improvements:

- `lua.c`: 60% -> 92%
- `loadlib.c`: 64% -> 75%
- `loslib.c`: 85% -> 89%

Lowest remaining line coverage after iteration 1:

- `lopcodes.c`: 53.8%, mostly opcode metadata helpers that are not directly
  reachable from normal CLI behavior.
- `linit.c`: 72.7%, remaining preload-only standard-library initialization path.
- `lmem.c`: 72.9%, allocation-failure/emergency-GC paths.
- `loadlib.c`: 75.4%, mostly successful dynamic C-library loading and symbol
  variants not exercised without shipping architecture-specific `.so` fixtures.
- `lzio.c`: 78.6%, low-level chunk reader address path.

## Repro commands

Harvested validation:

```bash
bash tasks/reproduced_lua/tests_harvested/eval/run.sh
```

Generated validation:

```bash
bash tasks/reproduced_lua/tests_generated/eval/run.sh
```

Generated quality gate:

```bash
bash tasks/reproduced_lua/scripts/quality_generated.sh
```

Rebuild downstream QC report from existing artifacts:

```bash
python3 tasks/reproduced_lua/scripts/build_qc_report.py
```

Harvested coverage:

```bash
bash tasks/reproduced_lua/scripts/coverage_harvested.sh
```

Generated coverage:

```bash
bash tasks/reproduced_lua/scripts/coverage_generated.sh
```
