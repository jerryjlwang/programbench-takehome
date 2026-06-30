# Lua Generated Suite QC Report

- Status: `passed`
- Generated at: `2026-06-30T06:21:14.080227+00:00`
- Active ProgramBench target: `1338`
- Generated gold pass count: `1338`
- Generated line coverage: `95.6%`
- Generated branch coverage: `89.1%`

## Linter checks

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

## Coverage line checks

| Check | Status | Observed | Target |
| --- | --- | ---: | ---: |
| generated_line_coverage_meets_local_target | passed | 95.6 | 95.0 |
| generated_line_coverage_not_lower_than_harvested | passed | 95.6 |  |
| generated_file_line_metrics_logged | passed | 32 |  |
| generated_full_line_coverage_json_logged | passed |  |  |
| harvested_full_line_coverage_json_logged | passed |  |  |

## LM-as-Judge Fairness Review

- Verdict: `latest_run_valid_but_failed_behavioral_eval`
- Subject run: `lua_miniswe_20260629_225007`
- Latest eval status: `failed`
- Latest eval passed: `7/1338`

| Check | Status | Blocking | Evidence |
| --- | --- | --- | --- |
| lm_as_judge_review_present | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/qc/lm_as_judge_review.json` |
| independent_lm_as_judge_review_completed | passed | True | `Explorer 019f1720-3b3f-7e71-9408-3de2c35f40b1 returned a verdict.` |
| latest_submission_not_disqualified_by_oracle_gate | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_225007/summary.json` |
| latest_submission_behavioral_eval_recorded | passed | True | `7/1338 tests passed; status failed.` |
| known_wrapper_submission_rejected | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_223354/summary.json` |
| solver_facing_task_env_has_no_tests_or_source | passed | True | `task_env contains only compile.sh, docs, and executable.` |
| solver_facing_task_env_has_no_git_directory | passed | True | `find task_env for .git returned no paths.` |
| test_suite_not_solver_facing | passed | True | `tests_generated is outside task_env and mounted only by evaluate_submission.sh.` |
| solve_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/run_miniswe_lua.py:87` |
| compile_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:87` |
| test_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:141` |
| prebuilt_submission_executable_ignored_before_compile | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:84` |
| stale_junit_results_removed_before_scoring | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:37` |
| trajectory_hidden_test_access_not_detected | passed | True | `No model-visible use of tests_generated/eval/tests paths found in the latest trajectory.` |
| trajectory_source_discovery_probe_absent | warning | False | `Unsuccessful local package/header/source probes present; see strict_trace_warnings.` |
| wrapper_pattern_scan_is_complete | risk | False | `Exact gold-byte and known-string scans are heuristic and should be supplemented by strict packaging.` |

### LM judge findings

| Severity | Status | Finding | Evidence |
| --- | --- | --- | --- |
| HIGH | resolved | The previous 36-call submission embedded and executed the gold oracle; the evaluator now rejects it before scoring. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_223354/summary.json` |
| MED | warning | The latest trajectory tried local package/header/source discovery commands, but no Lua source was found or used. Score the run as failed with a trace warning, not as disqualified. | `/Users/jerrywang/programbench-takehome/runs/lua_miniswe_20260629_225007/lua__lua.c6b4848/lua__lua.c6b4848.traj.json` |
| MED | resolved | The scoring container originally lacked explicit network isolation. The evaluator now uses an offline pytest image and reran the latest submission with --network none during scoring. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:141` |
| LOW | risk | Wrapper detection catches exact embedded gold bytes and known wrapper strings, but transformed encodings could evade static heuristics. Strict task packaging remains the primary defense. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:43` |
| LOW | accepted | Solver-facing docs identify Lua 5.5.1 behavior, which is necessary documentation rather than original source leakage. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/task_env/docs/USAGE.md` |
| INFO | observed | The latest scored run is a plausible failed reimplementation stub rather than a shortcut: it passed 7 of 1338 behavioral tests. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_225007/summary.json` |

## Lowest generated line coverage files

| File | Lines | Line coverage | Branch coverage |
| --- | ---: | ---: | ---: |
| lopcodes.c | 7/13 | 53.8% | 69.2% |
| linit.c | 8/11 | 72.7% | 60.0% |
| lmem.c | 43/59 | 72.9% | 64.3% |
| loadlib.c | 187/248 | 75.4% | 69.9% |
| lzio.c | 33/42 | 78.6% | 85.7% |
| lobject.c | 254/300 | 84.7% | 84.5% |
| loslib.c | 131/146 | 89.7% | 81.1% |
| lauxlib.c | 509/566 | 89.9% | 84.0% |
| lundump.c | 219/240 | 91.2% | 75.5% |
| ldblib.c | 230/250 | 92.0% | 80.9% |

## Raw artifact paths

- `quality_report`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/quality_generated/quality_report.json`
- `quality_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/logs/quality_generated.log`
- `gold_junit`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/quality_generated/gold_results.xml`
- `dummy_junit`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/quality_generated/dummy_results.xml`
- `coverage_generated_summary`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/coverage_generated/coverage_summary.json`
- `coverage_generated_full`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/coverage_generated/coverage.json`
- `coverage_generated_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/logs/coverage_generated.log`
- `coverage_harvested_summary`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/coverage_harvested/coverage_summary.json`
- `coverage_harvested_full`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/coverage_harvested/coverage.json`
- `coverage_harvested_log`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/logs/coverage_harvested.log`
- `lm_as_judge_review`: `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/qc/lm_as_judge_review.json`
