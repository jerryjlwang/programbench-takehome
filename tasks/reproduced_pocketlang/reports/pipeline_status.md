# PocketLang Pipeline Status

## Source Pin

- Repository: `ThakeeNathees/pocketlang`
- Commit: `cc73ca61b113d48ee130d837a7a8b145e41de5ce`
- Instance ID: `thakeenathees__pocketlang.cc73ca6`

## Gold Build

- Build script: `tasks/reproduced_pocketlang/scripts/build_gold.sh`
- Builder image: `gcc:13-bookworm`
- Platform: `linux/amd64`
- Gold executable: `tasks/reproduced_pocketlang/gold/pocket`
- Solver oracle copy: `tasks/reproduced_pocketlang/task_env/executable`
- SHA256: `2b6f181a9a47f7faee03f6171835abf3b5fca6532fc78bd6953a5af218e10a94`
- File type: ELF 64-bit x86-64 Linux executable

## Cleanroom Image

- Image: `programbench-pocketlang-cleanroom:local`
- Image ID: `sha256:1ff09735824512feb8d1b83077fbdf72d74c99b1acba77fc56337ad457d9fb1b`
- Image created: `2026-07-02T06:22:31.600801679Z`
- Solver-facing contents verified:
  - execute-only `./executable`
  - `./compile.sh`
  - `./docs/USAGE.md`
  - `./docs/help.txt`
  - `.gitignore`
- No original source, upstream tests, hidden tests, reports, logs, or `.git`
  metadata are present in `/workspace`.

## Smoke Checks

Verified inside the cleanroom image with `--network none`:

- `./executable --version` prints `pocketlang 0.1.0`
- `./executable --help` prints the expected CLI usage
- `./executable -c "print(1 + 2 * 3)"` prints `7`
- script-file execution works for a recursive Fibonacci sample
- `./compile.sh` preserves the protected oracle and builds `./candidate`
  while `./executable` is execute-only

## Harvested Suite

- Harvest source: pinned upstream `tests/` and `tests/examples/`
- Harvested manifest: `tasks/reproduced_pocketlang/tests_harvested/eval/cases/harvested_cases.json`
- Harvested upstream cases: 23
- Harvested eval result against gold: 25 pytest tests passed
- Harvested coverage: 68.0% line, 59.6% branch

## Generated Suite

- Generated manifest: `tasks/reproduced_pocketlang/tests_generated/eval/cases/generated_cases.json`
- Generated exact-output cases: 396
- Total generated-suite pytest tests: 421
- Generation strategy:
  - exact-output gold recording for non-empty observable behavior
  - harvested upstream suite retained as the base
  - coverage-guided additions for CLI parsing, command/script execution,
    control flow, closures, diagnostics, `types.ByteBuffer`, `types.Vector`,
    `os`, and `time`
  - runtime-dependent paths normalized to `<tmp>` and `<executable>`
- Generated eval result against gold: 421 passed
- Generated coverage: 72.7% line, 62.3% branch

## Quality And Fairness

- Assertion linter: 21 checks, 0 static findings
- Dynamic quality gate:
  - gold executable passed 421/421 tests
  - dummy executable passed 0/421 tests
- Deterministic fairness audit:
  `tasks/reproduced_pocketlang/reports/qc/deterministic_fairness_report.json`
- Fairness audit status: pass, 9 checks passed, 0 failed
- LM-as-judge fairness review:
  `tasks/reproduced_pocketlang/reports/qc/lm_as_judge_review.json`
- LM-as-judge verdict: `pre_agent_task_fairness_and_evaluator_checks_passed`
- Downstream QC report:
  `tasks/reproduced_pocketlang/reports/qc/generated_qc_report.json`
- Downstream QC status: passed, 0 failed blocking checks
- Hardened evaluator:
  `tasks/reproduced_pocketlang/scripts/evaluate_submission.sh`
- Evaluator smoke checks:
  - empty stub scored 0/421 and failed
  - version/help-only stub scored 3/421 and failed
- mini-SWE cleanroom runner:
  `tasks/reproduced_pocketlang/scripts/run_miniswe_pocketlang.sh`
- Runner readiness: `--help` entrypoint check passed through `uv run`
- Runner loop controls after first solve attempt:
  - 4-command cycles are blocked after 3 repeats
  - Gemini FormatError repair turns are capped at 8, then forced to submit
  - broad PocketLang smoke behavior is advisory at submit time; nontrivial
    built implementations are scored by the hardened evaluator
- Runner prompt normalization:
  - inherited ProgramBench "extensively test before writing code" guidance is
    replaced with a finite observe-then-implement, candidate-first instruction
- Post-compile candidate-first enforcement:
  - oracle calls are blocked after compile until `./candidate` has been run
  - at most 3 oracle calls are allowed between candidate checks
  - at most 20 total oracle calls are allowed after the first compile
- Runtime delegation source gate:
  - final submit is blocked when source uses `system`, `popen`, `exec*`,
    `posix_spawn`, external interpreter paths, or generated sibling runner
    scripts
  - clean `task_env` scan has 0 hits; a historical Python-delegating
    submission was flagged before cleanup
- Exact command substring-dispatch gate:
  - final submit is blocked when source dispatches on command/eval variables
    using `strstr`, `strcmp`, `strncmp`, `strcasestr`, `memcmp`, or `memmem`
  - normal CLI flag checks on `argv[1]` remain allowed
  - clean `task_env` scan has 0 hits; a historical substring-dispatch
    submission was flagged before cleanup
- Tainted command-buffer dispatch gate:
  - integrity scan tracks obvious `argv[2+]` aliases, function parameters
    called with `argv[2+]`, and copied buffers such as `cleaned[j++] = cmd[i]`
  - substring dispatch on those tainted buffers is blocked before scoring
  - clean `task_env` scan has 0 hits; a historical derived-buffer
    submission was flagged before cleanup
- Cleanroom image rebuilt after docs update and smoke-checked with
  `--network none`

## Finalized mini-SWE Eval

- Selected run: `pocketlang_miniswe_20260702_021259`
- Agent exit status: submitted
- Model: `gemini/gemini-3.5-flash`
- API calls: 142
- Reported cost: `$1.96416135`
- Hardened eval result:
  - 3/421 tests passed
  - 418 failures, 0 errors, 0 skipped
  - executable SHA256:
    `e7351ca37c99d5f489d480ff2975566cf47e335cfe4c26e4a14a7d810fa5350f`
- Final eval artifacts:
  `tasks/reproduced_pocketlang/reports/evals/pocketlang_miniswe_20260702_021259/`
- Final submission archive:
  `tasks/reproduced_pocketlang/reports/evals/pocketlang_miniswe_20260702_021259/submission.tar.gz`
