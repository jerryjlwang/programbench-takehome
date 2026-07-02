# Janet Deterministic Fairness Report

- Verdict: `pass`
- Blocking failures: `0`
- Warnings: `0`
- Generated cases: `307`
- Upstream suite scripts: `33`
- Upstream example flycheck scripts: `35`

## Checks

### python_wrappers_have_no_workspace_or_source_leaks

- Status: `pass`
- Evidence: No forbidden workspace/source strings in pytest wrappers.

### pytest_tests_use_run_janet_black_box_fixture

- Status: `pass`
- Evidence: Test wrappers avoid direct subprocess/source inspection and route behavior through run_janet.

### generated_cases_are_self_contained_eval_invocations

- Status: `pass`
- Evidence: 307 generated cases use --eval with explicit stdout/stderr/returncode and no path/env leaks.

### fixtures_have_no_workspace_absolute_path_leaks

- Status: `pass`
- Evidence: No local workspace/gold/_src absolute path leaks in hidden fixture files.

### native_source_fixtures_are_not_invoked_by_hidden_tests

- Status: `pass`
- Evidence: 4 native/example source fixture files exist but none are referenced by pytest parameter lists.

### upstream_fixtures_are_executable_inputs_not_candidate_introspection

- Status: `pass`
- Evidence: 33 suite scripts and 35 example scripts are passed as executable inputs under cwd, not used to inspect candidate source.

### solver_docs_name_hidden_behavior_families

- Status: `pass`
- Evidence: USAGE.md names the CLI and standard library behavior families covered by hidden tests.

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
- Evidence: Janet mini-SWE runner applies token/reasoning/observation caps, forces the named bash tool by default, recovers parser-raised Gemini FormatErrors into executable bash actions, strips Gemini thought metadata, removes commit instructions, enforces earlier persistent-source/build phases, rejects scratchpad heredocs and placeholder submissions, requires timeout-bounded generalized Janet smoke behavior including long eval/expression flags, rejects literal smoke hardcoding, and blocks oracle-inspection/git/network/package/system-search/repeated-command and repeated-command-cycle stagnation.

### test_harness_normalizes_environment_and_timing

- Status: `pass`
- Evidence: Harness sets LC_ALL=C, TZ=UTC, clears Janet path/profile env, and regexes suite duration.

## Notes
- This deterministic audit proves the hidden tests are black-box executable interactions, not direct candidate-source checks.
- It cannot prove that a short agent run will infer the full Janet language and standard library; it checks only that the behavior is observable through docs plus normal oracle execution.
