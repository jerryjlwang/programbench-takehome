# Lua Fairness LM-Judge Check

Judgment date: 2026-06-29

Scope distinction:

- Solver-facing task: `tasks/reproduced_lua/task_env`
- Full local recreation workspace: `tasks/reproduced_lua`

Overall verdict:

- `task_env` is fair/clean if it is the only directory provided to solvers.
- The full `tasks/reproduced_lua` workspace is not solver-safe and must not be
  exposed to solvers.

| Condition | Solver-facing `task_env` | Full local workspace | Evidence |
| --- | --- | --- | --- |
| No original source files in task | PASS | FAIL if exposed | `task_env` contains only `compile.sh`, docs, and `executable`; original Lua C/H source exists under `_src/lua/`. |
| No original tests in solver-facing task | PASS | FAIL if exposed | No test files or fixtures under `task_env`; upstream/generated tests exist under `tests_harvested/` and `tests_generated/`. |
| No `.git` directory | PASS | FAIL if exposed | No `.git` under `task_env`; `_src/lua/.git` exists in the local workspace. |
| No package metadata revealing original package unless needed for docs | PASS with caveat | FAIL if exposed | `task_env` has no package metadata; parent `task.yaml` reveals `repository: lua/lua` and commit. Docs identify Lua behavior, which is needed for solver usability. |
| No internet during solve | UNCLEAR / externally enforced | UNCLEAR | `task_env/compile.sh` is local-only, but network isolation depends on the solver runtime/container settings. |
| No access to the test suite | PASS if only `task_env` is mounted | FAIL if parent mounted | No tests in `task_env`; tests are sibling directories in the local workspace. |
| No direct path to the original repo | PASS with caveat | FAIL if exposed | Text search in `task_env` found no GitHub URL, commit, `_src`, or test path; `_src/lua/.git/config` in the local workspace contains the upstream remote URL. |

Required packaging rule:

Only package or mount `tasks/reproduced_lua/task_env` for the solver. Do not
include `tasks/reproduced_lua/_src`, `tests_harvested`, `tests_generated`,
`reports`, `logs`, `task.yaml`, repo-root guidance files, or nested `.git`
directories in the solve environment.

Recommended runtime rule:

Run the solve environment with network disabled at the container/runtime level,
for example Docker `--network none`, so the no-internet condition is enforced
during solving rather than inferred from local scripts.
