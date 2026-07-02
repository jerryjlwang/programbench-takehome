# Janet Generated Suite QC Report

- Status: `passed`
- Generated at: `2026-07-02T09:40:40.674609+00:00`
- Local generated tests: `381`
- Generated gold pass count: `381`
- Generated line coverage: `75.3%`
- Generated branch coverage: `68.5%`

## Dynamic Checks

| Check | Status | Observed |
| --- | --- | ---: |
| no_blocking_static_linter_findings | passed | 0 |
| gold_suite_passes | passed | 381 |
| dummy_suite_rejects | passed | 0 |

## Coverage Checks

| Check | Status | Observed | Target |
| --- | --- | ---: | ---: |
| generated_line_coverage_meets_local_target | passed | 75.3 | 75.0 |
| generated_line_coverage_not_lower_than_harvested | passed | 75.3 |  |
| generated_file_line_metrics_logged | passed | 41 |  |
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
| python_wrappers_have_no_workspace_or_source_leaks | pass | `No forbidden workspace/source strings in pytest wrappers.` |
| pytest_tests_use_run_janet_black_box_fixture | pass | `Test wrappers avoid direct subprocess/source inspection and route behavior through run_janet.` |
| generated_cases_are_self_contained_eval_invocations | pass | `307 generated cases use --eval with explicit stdout/stderr/returncode and no path/env leaks.` |
| fixtures_have_no_workspace_absolute_path_leaks | pass | `No local workspace/gold/_src absolute path leaks in hidden fixture files.` |
| native_source_fixtures_are_not_invoked_by_hidden_tests | pass | `4 native/example source fixture files exist but none are referenced by pytest parameter lists.` |
| upstream_fixtures_are_executable_inputs_not_candidate_introspection | pass | `33 suite scripts and 35 example scripts are passed as executable inputs under cwd, not used to inspect candidate source.` |
| solver_docs_name_hidden_behavior_families | pass | `USAGE.md names the CLI and standard library behavior families covered by hidden tests.` |
| solver_docs_explain_allowed_observation_boundary | pass | `USAGE.md explains black-box CLI observation and forbids binary/source shortcuts.` |
| solver_docs_explain_self_contained_runtime | pass | `USAGE.md states that hidden scoring runs only the compiled executable and requires a self-contained runtime.` |
| cleanroom_image_executes_oracle_without_read_permission | pass | `Cleanroom image root-owns the oracle, grants execute-only permission, preserves it during development builds via ./candidate, strips prebuilt executables from submissions, and solve runs with network disabled.` |
| solve_runner_enforces_context_budget_and_oracle_command_guards | pass | `Janet mini-SWE runner applies token/reasoning/observation caps, forces the named bash tool by default, recovers parser-raised Gemini FormatErrors into executable bash actions, strips Gemini thought metadata, removes commit instructions, enforces earlier persistent-source/build phases, rejects scratchpad heredocs and placeholder submissions, requires timeout-bounded generalized Janet smoke behavior including long eval/expression flags, rejects literal smoke hardcoding, and blocks oracle-inspection/git/network/package/system-search/repeated-command and repeated-command-cycle stagnation.` |
| test_harness_normalizes_environment_and_timing | pass | `Harness sets LC_ALL=C, TZ=UTC, clears Janet path/profile env, and regexes suite duration.` |

## LM-as-Judge Fairness Review

- Verdict: `latest_run_disqualified_oracle_embedding_task_fairness_checks_passed`
- Subject run: `janet_miniswe_20260630_142119`
- Latest eval status: `rejected_wrapper_or_oracle`
- Latest eval passed: `0/0`

| Check | Status | Blocking | Evidence |
| --- | --- | --- | --- |
| lm_as_judge_review_present | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/qc/lm_as_judge_review.json` |
| local_lm_as_judge_review_completed | passed | True | `Codex reviewed the Janet task recreation artifacts, deterministic fairness report, rejected solve summaries, and retained eval records.` |
| deterministic_fairness_audit_passed | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/qc/deterministic_fairness_report.json` |
| latest_submission_rejected_by_oracle_gate | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/evals/janet_miniswe_20260630_142119/summary.json` |
| latest_submission_behavioral_eval_not_scored_after_rejection | passed | True | `Rejected wrapper/oracle submissions are stopped before pytest scoring.` |
| downstream_miniswe_gemini_solve_attempt_summarized | passed | True | `tasks/reproduced_janet/reports/solve_attempts_summary.md` |
| retained_solve_summaries_show_no_hidden_test_leak | passed | True | `Retained eval summaries and LM review found no tests_generated/tests_harvested access before compacting raw trajectories.` |
| solver_facing_task_env_has_no_tests_or_source | passed | True | `task_env contains only compile.sh, docs, and executable.` |
| solver_facing_task_env_has_no_git_directory | passed | True | `find/rg scan of task_env found no .git paths.` |
| test_suite_not_solver_facing | passed | True | `tests_harvested and tests_generated are outside task_env and mounted only by evaluator/coverage scripts.` |
| task_env_path_leak_scan_clean | passed | True | `task_env scan found no GitHub URL, commit id, _src path, hidden tests, coverage path, or workspace path.` |
| solver_facing_docs_describe_compile_contract | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/task_env/docs/USAGE.md` |
| solver_facing_docs_describe_behavior_surface | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/task_env/docs/USAGE.md` |
| cleanroom_oracle_execute_only_configured | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/scripts/build_miniswe_cleanroom_image.sh` |
| solve_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/scripts/run_miniswe_janet.py` |
| compile_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/scripts/evaluate_submission.sh` |
| test_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/scripts/evaluate_submission.sh` |
| prebuilt_submission_executable_ignored_before_compile | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/scripts/evaluate_submission.sh` |
| stale_junit_results_removed_before_scoring | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/scripts/evaluate_submission.sh` |
| exact_gold_hash_rejection_configured | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/scripts/evaluate_submission.sh` |
| embedded_gold_oracle_scan_configured | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/scripts/evaluate_submission.sh` |
| bad_submission_behavioral_eval_recorded | passed | True | `Local bad stub submission scored 0/381 and failed, proving the suite rejects a trivial executable.` |

### LM judge findings

| Severity | Status | Finding | Evidence |
| --- | --- | --- | --- |
| HIGH | resolved_by_evaluator | The latest Janet solve trajectory embedded and delegated to the gold oracle; the evaluator rejected it before behavioral scoring. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/evals/janet_miniswe_20260630_142119/summary.json` |
| INFO | observed | Deterministic hidden-test fairness audit passes for the Janet generated suite and checks black-box test structure plus documentation sufficiency. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/qc/deterministic_fairness_report.json` |
| INFO | observed | The solver-facing Janet task_env contains only compile.sh, docs, and the oracle executable; hidden tests and source are outside the solve container. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/task_env` |
| LOW | accepted | Solver-facing docs identify Janet 1.41.2 behavior, the offline compile contract, the oracle observation boundary, and the end-to-end behavior surface. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/task_env/docs/USAGE.md` |

## Lowest Generated Line Coverage Files

| File | Lines | Line coverage | Branch coverage |
| --- | ---: | ---: | ---: |
| build/c/shell.c | 43/715 | 6.0% | 3.4% |
| src/core/run.c | 5/80 | 6.2% | 0.0% |
| src/core/wrap.c | 35/114 | 30.7% | 41.2% |
| src/core/state.c | 8/21 | 38.1% | 40.0% |
| src/core/ffi.c | 271/664 | 40.8% | 39.3% |
| src/core/net.c | 281/491 | 57.2% | 48.3% |
| src/core/debug.c | 129/219 | 58.9% | 52.6% |
| src/core/math.c | 130/199 | 65.3% | 73.8% |
| src/core/util.c | 322/483 | 66.7% | 66.4% |
| src/core/io.c | 296/443 | 66.8% | 57.8% |

## Raw Artifact Paths

- `quality_report`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/quality_generated/quality_report.json`
- `quality_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/logs/quality_generated.log`
- `gold_junit`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/quality_generated/gold_results.xml`
- `dummy_junit`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/quality_generated/dummy_results.xml`
- `coverage_generated_summary`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/coverage_generated/coverage_summary.json`
- `coverage_generated_full`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/coverage_generated/coverage.json`
- `coverage_generated_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/logs/coverage_generated.log`
- `coverage_harvested_summary`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/coverage_harvested/coverage_summary.json`
- `coverage_harvested_full`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/coverage_harvested/coverage.json`
- `coverage_harvested_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/logs/coverage_harvested.log`
- `fairness_report`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/fairness_lm_judge.md`
- `deterministic_fairness_report`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/qc/deterministic_fairness_report.json`
- `lm_as_judge_review`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_janet/reports/qc/lm_as_judge_review.json`
