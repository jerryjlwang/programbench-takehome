# Lua mini-SWE Submission Report: lua_miniswe_20260701_033746

## Run configuration

- Instance ID: `lua__lua.c6b4848`
- Model: `gemini/gemini-3.5-flash`
- Reasoning effort: `low`
- Max tokens per call: `4096`
- Tool choice: `bash`
- Observation character limit: `4000`
- Step limit: `1000`
- Wall-time limit: `7200` seconds
- Output directory: `runs/lua_miniswe_20260701_033746`

## Solve outcome

- Agent exit status: `Submitted`
- API calls: `154`
- Estimated model cost: `$2.4256686000000003`
- Format errors: `1`, recovered without repeated-format abort
- Benchmark guard blocks: `11`
- Submission archive: `runs/lua_miniswe_20260701_033746/lua__lua.c6b4848/submission.tar.gz`

This run is the current representative low-reasoning mini-SWE attempt for the
Lua task recreation. It is a useful benchmark artifact because the light
Gemini/mini-SWE scaffold completed a nontrivial cleanroom implementation attempt
without hitting the previous oracle-overwrite spiral or repeated-format abort.

## Evaluation outcome

- Hardened evaluator status: `failed`
- Tests passed: `180/1338`
- Tests failed: `1158`
- Test errors: `0`
- Test skipped: `0`
- Evaluator return code: `1`
- Candidate executable SHA256:
  `ef09a27e010a75dfac4339d6557b3cfdd50dd682e66a3a0ce5ec3d0ba9fb03ce`
- Pytest time: `111.194` seconds

Artifacts:

- Summary: `tasks/reproduced_lua/reports/evals/lua_miniswe_20260701_033746/summary.json`
- JUnit XML: `tasks/reproduced_lua/reports/evals/lua_miniswe_20260701_033746/results.xml`
- Pytest log: `tasks/reproduced_lua/reports/evals/lua_miniswe_20260701_033746/pytest.log`
- Compile log: `tasks/reproduced_lua/reports/evals/lua_miniswe_20260701_033746/compile.log`

## Notes

The submitted implementation is a Python-backed partial Lua runner embedded
through a C wrapper. It preserves the solve-time oracle during development by
building `./candidate`, then the evaluator rebuilds `./executable` from the
submission after stripping any prebuilt executable.

The run is not a successful solve, but it is materially stronger than the
earlier repeated-format, step-limit, and placeholder attempts: it submitted a
compiling non-oracle implementation and passed 180 generated behavioral tests.
