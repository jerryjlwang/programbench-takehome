# Janet Fairness LM-Judge Check

Judgment date: 2026-06-30

Scope distinction:

- Solver-facing task: `tasks/reproduced_janet/task_env`
- Full local recreation workspace: `tasks/reproduced_janet`

Overall verdict:

- `task_env` is fair/clean if it is the only directory provided to solvers.
- The full `tasks/reproduced_janet` workspace is not solver-safe and must not
  be exposed to solvers.

| Condition | Solver-facing `task_env` | Full local workspace | Evidence |
| --- | --- | --- | --- |
| No original source files in task | PASS | FAIL if exposed | `task_env` contains only `compile.sh`, docs, and `executable`; original Janet C/Janet source exists under `_src/janet/`. |
| No original tests in solver-facing task | PASS | FAIL if exposed | No test files or fixtures under `task_env`; upstream/generated tests exist under `tests_harvested/` and `tests_generated/`. |
| No `.git` directory | PASS | PASS for `_src` snapshot | No `.git` under `task_env`; the pinned `_src/janet` snapshot has its nested clone metadata removed. |
| No package metadata revealing original package unless needed for docs | PASS with caveat | FAIL if exposed | `task_env` has no package metadata; parent `task.yaml` reveals `repository: janet-lang/janet` and commit. Docs identify Janet behavior, which is needed for solver usability. |
| No internet during solve | ENFORCED BY SCRIPTS | UNCLEAR if bypassed | `run_miniswe_janet.py` and `evaluate_submission.sh` use Docker `--network none` for solve, compile, and scoring flows. |
| No access to the test suite | PASS if only `task_env` is mounted | FAIL if parent mounted | No tests in `task_env`; tests are sibling directories in the local workspace. |
| No direct path to the original repo | PASS with caveat | FAIL if exposed | Text search in `task_env` should find no GitHub URL, commit, `_src`, or test path; `_src` contents remain available in the local workspace for build/coverage only. |

Required packaging rule:

Only package or mount `tasks/reproduced_janet/task_env` for the solver. Do not
include `tasks/reproduced_janet/_src`, `tests_harvested`, `tests_generated`,
`reports`, `logs`, `task.yaml`, repo-root guidance files, or hidden test
fixtures in the solve environment.

Recommended runtime rule:

Run the solve environment with network disabled at the container/runtime level,
for example Docker `--network none`, so the no-internet condition is enforced
during solving rather than inferred from local scripts.
