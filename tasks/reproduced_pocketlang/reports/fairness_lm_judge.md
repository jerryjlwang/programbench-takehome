# PocketLang Fairness LM-Judge Check

Judgment date: 2026-07-02

Scope distinction:

- Solver-facing task: `tasks/reproduced_pocketlang/task_env`
- Full local recreation workspace: `tasks/reproduced_pocketlang`

Overall verdict:

- `task_env` is fair/clean if it is the only directory provided to solvers.
- The full `tasks/reproduced_pocketlang` workspace is not solver-safe and must
  not be exposed to solvers.

| Condition | Solver-facing `task_env` | Full local workspace | Evidence |
| --- | --- | --- | --- |
| No original source files in task | PASS | FAIL if exposed | `task_env` contains only `compile.sh`, docs, and `executable`; original PocketLang source exists under `_src/pocketlang/`. |
| No original tests in solver-facing task | PASS | FAIL if exposed | No test files or fixtures under `task_env`; harvested/generated tests exist under `tests_harvested/` and `tests_generated/`. |
| No `.git` directory | PASS | FAIL if exposed | No `.git` under `task_env`; `_src/pocketlang/.git` exists in the local workspace. |
| No package metadata revealing original package unless needed for docs | PASS with caveat | FAIL if exposed | `task_env` has no package metadata; parent `task.yaml` reveals repository and commit. Docs identify PocketLang behavior, which is needed for solver usability. |
| No internet during solve | PASS if cleanroom runner is used | UNCLEAR outside runner | The cleanroom image was smoke-checked with `--network none`; solve isolation must mount only `task_env`. |
| No access to the test suite | PASS if only `task_env` is mounted | FAIL if parent mounted | Hidden tests are outside `task_env` and mounted only by evaluation/coverage scripts. |
| No direct path to the original repo | PASS with caveat | FAIL if exposed | Deterministic fairness audit found no local workspace, source, gold, repository URL, or commit leaks in pytest wrappers or case manifests. |

Required packaging rule:

Only package or mount `tasks/reproduced_pocketlang/task_env` for the solver. Do
not include `tasks/reproduced_pocketlang/_src`, `tests_harvested`,
`tests_generated`, `reports`, `logs`, `task.yaml`, repo-root guidance files, or
nested `.git` directories in the solve environment.

Recommended runtime rule:

Run the solve environment with network disabled at the container/runtime level,
for example Docker `--network none`, so the no-internet condition is enforced
during solving rather than inferred from local scripts.
