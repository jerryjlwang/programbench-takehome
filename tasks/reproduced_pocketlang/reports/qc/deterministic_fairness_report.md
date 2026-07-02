# PocketLang Deterministic Fairness Audit

- Status: `pass`
- Checks: 9 passed, 0 failed
- Harvested cases: 23
- Generated cases: 396
- Generated coverage: 72.7% line, 62.3% branch

## Checks

- `pass` `task_env_contains_only_solver_facing_files`: task_env contains only executable, compile.sh, and docs.
- `pass` `solver_docs_cover_hidden_behavior_families`: USAGE.md names the CLI, language, standard-library, error, and runtime boundaries covered by hidden tests.
- `pass` `solver_docs_explain_black_box_observation_boundary`: USAGE.md forbids binary/source shortcuts and limits observation to CLI behavior.
- `pass` `pytest_wrappers_have_no_workspace_source_leaks`: No local workspace, source, gold, repository URL, or commit leaks in pytest wrappers.
- `pass` `pytest_tests_route_behavior_through_run_pocket`: Test wrappers avoid direct subprocess/source inspection and route behavior through the run_pocket fixture.
- `pass` `pytest_assertions_compare_exact_observable_behavior`: Wrappers assert exact return code, stdout, and stderr instead of broad substring checks.
- `pass` `case_manifests_are_exact_self_contained_and_large_enough`: 23 harvested cases and 396 generated cases have exact outputs, unique ids, no local path leaks, and non-empty observable behavior.
- `pass` `quality_gate_gold_passes_dummy_rejected`: Gold passed 421 tests with 0 failures; dummy passed 0 and failed 421.
- `pass` `generated_suite_preserves_or_improves_coverage`: Harvested coverage 68.0% line/59.6% branch; generated coverage 72.7% line/62.3% branch.
