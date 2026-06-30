# LM-as-Judge Fairness Review

- Verdict: `latest_run_valid_but_failed_behavioral_eval`
- Subject run: `lua_miniswe_20260629_225007`
- Latest scored result: `7/1338` passed, `1331` failed
- Previous wrapper run: `rejected_wrapper_or_oracle`

## Findings

| Severity | Status | Finding | Evidence |
| --- | --- | --- | --- |
| HIGH | resolved | Previous 36-call submission embedded and executed the gold oracle; the evaluator now rejects it before scoring. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_223354/summary.json` |
| MED | warning | Latest trajectory tried local package/header/source discovery commands, but no Lua source was found or used. Score as failed with a trace warning, not as disqualified. | `/Users/jerrywang/programbench-takehome/runs/lua_miniswe_20260629_225007/lua__lua.c6b4848/lua__lua.c6b4848.traj.json` |
| MED | resolved | Scoring originally lacked explicit network isolation. The evaluator now uses an offline pytest image and reran the latest submission with `--network none`. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:141` |
| LOW | risk | Wrapper detection is heuristic beyond exact gold-byte and known wrapper-string scans. Strict packaging remains the primary defense. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/scripts/evaluate_submission.sh:43` |
| LOW | accepted | Solver-facing docs identify Lua 5.5.1 behavior, which is necessary documentation rather than original source leakage. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/task_env/docs/USAGE.md` |
| INFO | observed | Latest scored run is a plausible failed reimplementation stub rather than a shortcut. | `/Users/jerrywang/programbench-takehome/tasks/reproduced_lua/reports/evals/lua_miniswe_20260629_225007/summary.json` |

## Blocking Checks

All blocking LM-as-judge checks pass:

- Latest submission is fair to score and failed normally.
- Previous oracle wrapper submission is rejected.
- Solver-facing `task_env` has no tests, source, or `.git` directory.
- Solve, compile, and scoring containers use network-disabled execution.
- Prebuilt submitted `executable` files are removed before compile.
- Stale JUnit files are removed before scoring.
- No model-visible hidden test access was detected in the latest trajectory.

