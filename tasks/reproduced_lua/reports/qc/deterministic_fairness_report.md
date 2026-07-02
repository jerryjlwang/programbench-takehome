# Lua Deterministic Fairness Report

- Verdict: `pass`
- Blocking failures: `0`
- Warnings: `0`
- Generated cases: `1306`
- Upstream Lua input scripts: `28`
- Native fixture files not compiled by tests: `6`

## Checks

### python_wrappers_have_no_workspace_or_source_leaks

- Status: `pass`
- Evidence: No forbidden workspace/source strings in pytest wrappers.

### pytest_tests_use_run_lua_black_box_fixture

- Status: `pass`
- Evidence: Test wrappers avoid direct subprocess/source inspection and route behavior through run_lua.

### generated_cases_are_self_contained_eval_invocations

- Status: `pass`
- Evidence: 1306 generated cases use -e with explicit stdout/stderr/returncode and no path/env leaks.

### fixtures_have_no_workspace_absolute_path_leaks

- Status: `pass`
- Evidence: No local workspace/gold/_src absolute path leaks in hidden fixture files.

### native_source_fixtures_are_not_compiled_by_hidden_tests

- Status: `pass`
- Evidence: 6 native fixture files exist but pytest wrappers do not compile or name them.

### upstream_user_suite_runs_user_mode_without_internal_c_api

- Status: `pass`
- Evidence: The upstream suite is invoked with _U=true and all.lua disables internal T/C API checks.

### upstream_fixtures_are_executable_inputs_not_candidate_introspection

- Status: `pass`
- Evidence: 28 upstream Lua scripts are passed to the executable under cwd, not used to inspect candidate source.

### solver_docs_name_hidden_behavior_families

- Status: `pass`
- Evidence: USAGE.md names the CLI, language, runtime, and standard-library behavior families covered by hidden tests.

### solver_docs_explain_allowed_observation_boundary

- Status: `pass`
- Evidence: USAGE.md explains black-box CLI observation and forbids binary/source shortcuts.

### solver_docs_explain_self_contained_runtime

- Status: `pass`
- Evidence: USAGE.md states that hidden scoring runs only the compiled executable and requires a self-contained runtime.

### cleanroom_image_executes_oracle_without_read_permission

- Status: `pass`
- Evidence: Cleanroom image root-owns the oracle, grants execute-only permission, preserves it during development builds via ./candidate, strips prebuilt executables from submissions, and solve runs with network disabled.

### solve_runner_enforces_context_budget_and_oracle_command_guards

- Status: `pass`
- Evidence: Lua mini-SWE runner applies token/reasoning/observation caps, forces the named bash tool by default, strips Gemini thought metadata, removes commit instructions, enforces source-first/build phases, rejects placeholder submissions, and blocks oracle-inspection/scratchpad/git/network/package/system-search/repeated-command stagnation.

### test_harness_normalizes_environment_and_avoids_timing_or_seed_exactness

- Status: `pass`
- Evidence: Harness sets LC_ALL=C/TZ=UTC and checks suite completion without pinning random seed or timing values.

## Notes
- This deterministic audit proves the hidden tests are black-box executable interactions, not direct candidate-source checks.
- It cannot prove that a short agent run will infer the full Lua language and standard library; it checks only that the behavior is observable through docs plus normal oracle execution.
