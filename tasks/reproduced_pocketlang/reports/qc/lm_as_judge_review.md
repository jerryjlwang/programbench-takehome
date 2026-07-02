# PocketLang LM-as-Judge Fairness Review

- Verdict: `pre_agent_task_fairness_and_evaluator_checks_passed`
- Reviewer: `Codex LM-as-judge local fairness audit`
- Generated at: `2026-07-02T06:45:56Z`
- Subject run: `pre_agent_empty_stub_smoke`
- Latest eval status: `failed`
- Latest eval passed: `0/421`

## Checks

| Check | Status | Blocking | Evidence |
| --- | --- | --- | --- |
| local_lm_as_judge_review_completed | passed | True | `Codex reviewed the PocketLang task recreation artifacts, deterministic fairness report, cleanroom image, generated suite, hardened evaluator, mini-SWE runner, and bad-stub eval.` |
| deterministic_fairness_audit_passed | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/qc/deterministic_fairness_report.json` |
| generated_quality_gate_gold_passes_dummy_rejects | passed | True | `Gold passed 421/421 generated-suite tests; dummy passed 0/421.` |
| generated_suite_above_programbench_minimum | passed | True | `421 total generated-suite pytest tests and 396 generated exact-output cases; above the 224-test ProgramBench minimum referenced by the project.` |
| bad_stub_behavioral_eval_recorded | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/evals/pocketlang_empty_stub/summary.json: empty stub scored 0/421 and failed.` |
| solver_facing_task_env_has_no_tests_or_source | passed | True | `task_env contains only compile.sh, docs, and executable.` |
| solver_facing_task_env_has_no_git_directory | passed | True | `find/rg scan of task_env found no .git paths.` |
| test_suite_not_solver_facing | passed | True | `tests_harvested and tests_generated are outside task_env and mounted only by evaluation/coverage scripts.` |
| task_env_path_leak_scan_clean | passed | True | `Deterministic audit found no local workspace, source, gold, repository URL, commit, hidden-test, coverage, or report leaks in solver-facing wrappers/manifests.` |
| solver_facing_docs_describe_compile_contract | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/task_env/docs/USAGE.md` |
| solver_facing_docs_describe_behavior_surface | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/task_env/docs/USAGE.md` |
| cleanroom_oracle_execute_only_configured | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/build_miniswe_cleanroom_image.sh` |
| cleanroom_image_smoke_checked_network_none | passed | True | `programbench-pocketlang-cleanroom:local was rebuilt and smoke-checked with --network none; only expected workspace files were present.` |
| solve_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/run_miniswe_pocketlang.py` |
| compile_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/evaluate_submission.sh` |
| test_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/evaluate_submission.sh` |
| prebuilt_submission_executable_ignored_before_compile | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/evaluate_submission.sh` |
| stale_junit_results_removed_before_scoring | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/evaluate_submission.sh` |
| exact_gold_hash_rejection_configured | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/evaluate_submission.sh` |
| embedded_gold_oracle_scan_configured | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/evaluate_submission.sh` |
| downstream_miniswe_runner_imports_and_help_work | passed | True | `/tmp/pocketlang_miniswe_help.log` |
| downstream_miniswe_solve_not_yet_run | not_applicable | False | `PocketLang mini-SWE solve is ready but has not been started.` |

## Strict Trace Warnings

| Severity | Status | ID | Evidence |
| --- | --- | --- | --- |
| INFO | not_applicable | no_solve_trajectory_yet | `PocketLang solve/eval has not been run yet.` |

## Findings

| Severity | Status | Finding | Evidence |
| --- | --- | --- | --- |
| INFO | observed | Deterministic hidden-test fairness audit passes for the PocketLang generated suite and checks black-box test structure plus documentation sufficiency. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/qc/deterministic_fairness_report.json` |
| INFO | observed | The solver-facing PocketLang task_env contains only compile.sh, docs, and the oracle executable; hidden tests and source are outside the solve container. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/task_env` |
| INFO | observed | Generated tests are exact-output behavioral tests that run the candidate executable via pytest wrappers and reject a dummy implementation. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/quality_generated/quality_report.json` |
| INFO | observed | The hardened evaluator compiles offline with --network none, removes prebuilt executables, rejects gold hash/embedded oracle bytes, and scored an empty stub at 0/421. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/evals/pocketlang_empty_stub/summary.json` |
| LOW | accepted | Solver-facing docs identify PocketLang 0.1.0 behavior, the offline compile contract, the oracle observation boundary, and the end-to-end behavior surface. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/task_env/docs/USAGE.md` |
| INFO | pending | No PocketLang mini-SWE solve trajectory exists yet; trajectory-specific fairness checks should be rerun after the first solve/eval. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/run_miniswe_pocketlang.py` |

## Solver Environment Manifest
- `task_env/compile.sh`
- `task_env/docs/USAGE.md`
- `task_env/docs/help.txt`
- `task_env/executable`
