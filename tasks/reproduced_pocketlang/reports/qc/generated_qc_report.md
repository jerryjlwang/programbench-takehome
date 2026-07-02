# PocketLang Generated Suite QC Report

- Status: `passed`
- Generated at: `2026-07-02T06:45:56.126628+00:00`
- Local generated tests: `421`
- Generated gold pass count: `421`
- Generated line coverage: `72.7%`
- Generated branch coverage: `62.3%`

## Dynamic Checks

| Check | Status | Observed |
| --- | --- | ---: |
| no_blocking_static_linter_findings | passed | 0 |
| gold_suite_passes | passed | 421 |
| dummy_suite_rejects | passed | 0 |

## Coverage Checks

| Check | Status | Observed | Target |
| --- | --- | ---: | ---: |
| generated_line_coverage_meets_local_target | passed | 72.7 | 72.0 |
| generated_line_coverage_not_lower_than_harvested | passed | 72.7 |  |
| generated_file_line_metrics_logged | passed | 20 |  |
| generated_full_line_coverage_json_logged | passed |  |  |
| harvested_full_line_coverage_json_logged | passed |  |  |

## Linter Checks

| Check | Severity | Status | Findings | Blocking findings |
| --- | --- | --- | ---: | ---: |
| no_assertions | HIGH | passed | 0 | 0 |
| trivially_true | HIGH | passed | 0 | 0 |
| sole_returncode | HIGH | passed | 0 | 0 |
| returncode_in_list | HIGH | passed | 0 | 0 |
| pass_body | HIGH | passed | 0 | 0 |
| assertion_disjunction | HIGH | passed | 0 | 0 |
| if_no_else | HIGH | passed | 0 | 0 |
| if_else_both_assert | HIGH | passed | 0 | 0 |
| try_except_swallow | HIGH | passed | 0 | 0 |
| all_assertions_weak | HIGH | passed | 0 | 0 |
| short_substring | HIGH | passed | 0 | 0 |
| golden_written_in_test | HIGH | passed | 0 | 0 |
| golden_no_equality | HIGH | passed | 0 | 0 |
| golden_docstring | HIGH | passed | 0 | 0 |
| for_no_guard | MED | passed | 0 | 0 |
| weak_sole_assertion | MED | passed | 0 | 0 |
| relative_length_assertion | MED | passed | 0 | 0 |
| any_all_no_guard | MED | passed | 0 | 0 |
| file_exists_no_content | MED | passed | 0 | 0 |
| only_negative_assertions | MED | passed | 0 | 0 |
| catches | LOW | informational | 0 | 0 |

## Deterministic Fairness Review

- Verdict: `pass`
- Blocking failures: `0`
- Warnings: `0`

| Check | Status | Evidence |
| --- | --- | --- |
| task_env_contains_only_solver_facing_files | pass | `task_env contains only executable, compile.sh, and docs.` |
| solver_docs_cover_hidden_behavior_families | pass | `USAGE.md names the CLI, language, standard-library, error, and runtime boundaries covered by hidden tests.` |
| solver_docs_explain_black_box_observation_boundary | pass | `USAGE.md forbids binary/source shortcuts and limits observation to CLI behavior.` |
| pytest_wrappers_have_no_workspace_source_leaks | pass | `No local workspace, source, gold, repository URL, or commit leaks in pytest wrappers.` |
| pytest_tests_route_behavior_through_run_pocket | pass | `Test wrappers avoid direct subprocess/source inspection and route behavior through the run_pocket fixture.` |
| pytest_assertions_compare_exact_observable_behavior | pass | `Wrappers assert exact return code, stdout, and stderr instead of broad substring checks.` |
| case_manifests_are_exact_self_contained_and_large_enough | pass | `23 harvested cases and 396 generated cases have exact outputs, unique ids, no local path leaks, and non-empty observable behavior.` |
| quality_gate_gold_passes_dummy_rejected | pass | `Gold passed 421 tests with 0 failures; dummy passed 0 and failed 421.` |
| generated_suite_preserves_or_improves_coverage | pass | `Harvested coverage 68.0% line/59.6% branch; generated coverage 72.7% line/62.3% branch.` |

## LM-as-Judge Fairness Review

- Verdict: `pre_agent_task_fairness_and_evaluator_checks_passed`
- Subject run: `pre_agent_empty_stub_smoke`
- Latest eval status: `failed`
- Latest eval passed: `0/421`

| Check | Status | Blocking | Evidence |
| --- | --- | --- | --- |
| lm_as_judge_review_present | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/qc/lm_as_judge_review.json` |
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
| downstream_miniswe_solve_completed | passed | True | `pocketlang_miniswe_20260702_021259: 3/421 tests passed (418 failed, returncode 1) — solver compiled but could not reproduce PocketLang behavior.` |

### LM judge findings

| Severity | Status | Finding | Evidence |
| --- | --- | --- | --- |
| INFO | observed | Deterministic hidden-test fairness audit passes for the PocketLang generated suite and checks black-box test structure plus documentation sufficiency. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/qc/deterministic_fairness_report.json` |
| INFO | observed | The solver-facing PocketLang task_env contains only compile.sh, docs, and the oracle executable; hidden tests and source are outside the solve container. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/task_env` |
| INFO | observed | Generated tests are exact-output behavioral tests that run the candidate executable via pytest wrappers and reject a dummy implementation. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/quality_generated/quality_report.json` |
| INFO | observed | The hardened evaluator compiles offline with --network none, removes prebuilt executables, rejects gold hash/embedded oracle bytes, and scored an empty stub at 0/421. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/evals/pocketlang_empty_stub/summary.json` |
| LOW | accepted | Solver-facing docs identify PocketLang 0.1.0 behavior, the offline compile contract, the oracle observation boundary, and the end-to-end behavior surface. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/task_env/docs/USAGE.md` |
| INFO | pending | No PocketLang mini-SWE solve trajectory exists yet; trajectory-specific fairness checks should be rerun after the first solve/eval. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/scripts/run_miniswe_pocketlang.py` |

## Lowest Generated Line Coverage Files

| File | Lines | Line coverage | Branch coverage |
| --- | ---: | ---: | ---: |
| src/libs/gen/nativeapi.h | 0/60 | 0.0% | None% |
| src/core/debug.c | 108/352 | 30.7% | 34.7% |
| src/libs/std_io.c | 96/218 | 44.0% | 24.7% |
| src/core/utils.c | 97/168 | 57.7% | 54.1% |
| cli/argparse.h | 133/229 | 58.1% | 53.4% |
| src/libs/std_term.c | 107/180 | 59.4% | 3.8% |
| src/libs/std_os.c | 61/93 | 65.6% | 51.4% |
| src/core/core.c | 773/1173 | 65.9% | 54.2% |
| src/core/public.c | 323/485 | 66.6% | 49.7% |
| src/libs/std_path.c | 105/153 | 68.6% | 55.4% |

## Raw Artifact Paths

- `quality_report`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/quality_generated/quality_report.json`
- `quality_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/logs/quality_generated.log`
- `gold_junit`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/quality_generated/gold_results.xml`
- `dummy_junit`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/quality_generated/dummy_results.xml`
- `coverage_generated_summary`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/coverage_generated/coverage_summary.json`
- `coverage_generated_full`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/coverage_generated/coverage.json`
- `coverage_generated_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/logs/coverage_generated.log`
- `coverage_harvested_summary`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/coverage_harvested/coverage_summary.json`
- `coverage_harvested_full`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/coverage_harvested/coverage.json`
- `coverage_harvested_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/logs/coverage_harvested.log`
- `fairness_report`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/fairness_lm_judge.md`
- `deterministic_fairness_report`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/qc/deterministic_fairness_report.json`
- `lm_as_judge_review`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_pocketlang/reports/qc/lm_as_judge_review.json`
