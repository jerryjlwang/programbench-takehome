# Lua LM-as-Judge Fairness Review

- Verdict: `latest_run_valid_but_failed_behavioral_eval`
- Reviewer: `Codex LM-as-judge with independent explorer review`
- Generated at: `2026-06-30T23:15:59Z`
- Subject run: `lua_miniswe_20260629_225007`
- Latest eval status: `failed`
- Latest eval passed: `7/1338`

## Checks

| Check | Status | Blocking | Evidence |
| --- | --- | --- | --- |
| independent_lm_as_judge_review_completed | passed | True | `Explorer 019f1720-3b3f-7e71-9408-3de2c35f40b1 returned a verdict.` |
| latest_submission_not_disqualified_by_oracle_gate | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_225007/summary.json` |
| latest_submission_behavioral_eval_recorded | passed | True | `7/1338 tests passed; status failed.` |
| known_wrapper_submission_rejected | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_223354/summary.json` |
| solver_facing_task_env_has_no_tests_or_source | passed | True | `task_env contains only compile.sh, docs, and executable.` |
| solver_facing_task_env_has_no_git_directory | passed | True | `find task_env for .git returned no paths.` |
| test_suite_not_solver_facing | passed | True | `tests_generated is outside task_env and mounted only by evaluate_submission.sh.` |
| solver_facing_docs_describe_compile_contract | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/task_env/docs/USAGE.md documents offline gcc:13-bookworm compile, network-disabled build, and required ./executable output.` |
| solver_facing_docs_describe_behavior_surface | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/task_env/docs/USAGE.md describes CLI options, oracle observation, script/stdin/module/environment/error behavior, and core standard-library behavior families.` |
| solve_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/run_miniswe_lua.py:87` |
| compile_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:87` |
| test_network_disabled | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:141` |
| prebuilt_submission_executable_ignored_before_compile | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:84` |
| stale_junit_results_removed_before_scoring | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:37` |
| trajectory_hidden_test_access_not_detected | passed | True | `No model-visible use of tests_generated/eval/tests paths found in the latest trajectory.` |
| trajectory_source_discovery_probe_absent | warning | False | `Unsuccessful local package/header/source probes present; see strict_trace_warnings.` |
| wrapper_pattern_scan_is_complete | risk | False | `Exact gold-byte and known-string scans are heuristic and should be supplemented by strict packaging.` |
| deterministic_fairness_audit_passed | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/qc/deterministic_fairness_report.json` |
| cleanroom_oracle_execute_only_configured | passed | True | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/build_miniswe_cleanroom_image.sh` |

## Strict Trace Warnings

| Severity | Status | ID | Evidence |
| --- | --- | --- | --- |
| MED | warning | unsuccessful_local_source_discovery_probe | `/Users/jerrywang/programbench-takehome/runs/lua_miniswe_20260629_225007/lua__lua.c6b4848/lua__lua.c6b4848.traj.json` |

## Findings

| Severity | Status | Finding | Evidence |
| --- | --- | --- | --- |
| INFO | observed | Deterministic hidden-test fairness audit now passes before future solve runs. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/qc/deterministic_fairness_report.json` |
| HIGH | resolved | The previous 36-call submission embedded and executed the gold oracle; the evaluator now rejects it before scoring. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_223354/summary.json` |
| MED | warning | The latest trajectory tried local package/header/source discovery commands, but no Lua source was found or used. Score the run as failed with a trace warning, not as disqualified. | `/Users/jerrywang/programbench-takehome/runs/lua_miniswe_20260629_225007/lua__lua.c6b4848/lua__lua.c6b4848.traj.json` |
| MED | resolved | The scoring container originally lacked explicit network isolation. The evaluator now uses an offline pytest image and reran the latest submission with --network none during scoring. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:141` |
| LOW | risk | Wrapper detection catches exact embedded gold bytes and known wrapper strings, but transformed encodings could evade static heuristics. Strict task packaging remains the primary defense. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:43` |
| LOW | accepted | Solver-facing docs identify Lua 5.5.1 behavior and document the offline compile contract plus end-to-end behavior surface, which is necessary documentation rather than original source leakage. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/task_env/docs/USAGE.md` |
| INFO | observed | The latest scored run is a plausible failed reimplementation stub rather than a shortcut: it passed 7 of 1338 behavioral tests. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_225007/summary.json` |

## Solver Environment Manifest
- `task_env/compile.sh`
- `task_env/docs/USAGE.md`
- `task_env/docs/help.txt`
- `task_env/executable`
