# Janet Task Recreation Status

## Target

- Repository: janet-lang/janet
- Pinned tag: v1.41.2
- Pinned commit: 0fea20c82182fe661f75b00a8889d801fe2d79b6
- Instance ID: janet-lang__janet.0fea20c
- Gold executable: tasks/reproduced_janet/gold/janet
- Gold SHA256: 0803a73d40bcce61c07950d509d023d40ccc896fff3ca57571a4194377678235

## Created Artifacts

- Pinned source clone for build and coverage only: tasks/reproduced_janet/_src/janet
- Solver-facing cleanroom: tasks/reproduced_janet/task_env
- Harvested behavioral tests: tasks/reproduced_janet/tests_harvested
- Generated behavioral tests: tasks/reproduced_janet/tests_generated
- Quality gate and evaluator scripts: tasks/reproduced_janet/scripts
- QC report: tasks/reproduced_janet/reports/qc/generated_qc_report.json

## Validation Results

- Gold build: succeeded; `janet --version` reports `1.41.2-0fea20c8`.
- Harvested suite against gold: 71 passed.
- Generated suite against gold: 381 passed, including 307 coverage-guided generated cases layered on the harvested baseline.
- Harvested coverage: 75.1% line, 68.4% branch.
- Generated coverage: 75.3% line, 68.5% branch.
- Quality gate: gold passed all 381 tests; dummy executable passed 0 tests; static assertion linter reported 0 findings.
- QC report: passed.
- Cleanroom image: built as `programbench-janet-cleanroom:local`.
- Fairness leak scan of task_env: no source, tests, coverage, commit, GitHub URL, or workspace paths found.
- LM-as-judge fairness review: local packaging, leakage, offline execution, compile-contract, behavior-surface audit, and the inspected rejected mini-SWE trajectory passed in `reports/qc/lm_as_judge_review.json`.
- Evaluator smoke test: compiled a bad stub submission offline and rejected it with 381/381 behavioral failures.

## mini-SWE prep status

- Runner syntax check: passed.
- Deterministic fairness check: passed.
- Cleanroom image: `programbench-janet-cleanroom:local`.
- Cleanroom image ID:
  `sha256:1a941047a5f90888e66caa5570cb6240c2d18f9fc1276d7416cb6a379d008694`.
- Cleanroom image created: `2026-07-01T10:32:12.802099668Z`.
- Oracle smoke check: `./executable --version` reports `1.41.2-0fea20c8`.
- Candidate-preservation smoke check: while protected `./executable` is
  present, `./compile.sh` builds `./candidate` and leaves the oracle intact.
- Runner guard status: Gemini context cleanup, parser-raised FormatError repair,
  forced bash tool choice, earlier persistent-source phase gate, earlier
  build-phase gate, scratchpad heredoc rejection, placeholder submission
  rejection, timeout-bounded generalized Janet behavior smoke gate with long
  `--eval`/`--expression` flag coverage, literal smoke-hardcode rejection,
  oracle-inspection blocks, system-search/package/network blocks, repeated
  command-cycle stagnation blocking, and submission archive stripping are
  enabled.

## mini-SWE attempt outcome

- Solve attempt summary:
  `tasks/reproduced_janet/reports/solve_attempts_summary.md`
- Early runs were rejected by the hardened evaluator for exact oracle bytes,
  embedded binary data, or wrapper/oracle patterns.
- Later non-oracle submissions compiled but scored between 0/381 and 1/381.
- Janet was retained as a useful record of scaffold hardening, but the final
  take-home demonstration pivoted to PocketLang because the lightweight Gemini
  mini-SWE agent could not produce a meaningful Janet reimplementation.

Recommended next solve settings mirror the representative Lua run:

- Model: `gemini/gemini-3.5-flash`
- Reasoning effort: `low`
- Max tokens per call: `2048`
- Tool choice: `bash`
- Observation character limit: `4000`
- Step limit: `1000`
- Wall-time limit: `7200` seconds

## Primary Commands

```bash
bash tasks/reproduced_janet/scripts/build_gold.sh
bash tasks/reproduced_janet/scripts/coverage_harvested.sh
bash tasks/reproduced_janet/scripts/coverage_generated.sh
bash tasks/reproduced_janet/scripts/quality_generated.sh
python3 tasks/reproduced_janet/scripts/build_qc_report.py
bash tasks/reproduced_janet/scripts/build_miniswe_cleanroom_image.sh programbench-janet-cleanroom:local
bash tasks/reproduced_janet/scripts/evaluate_submission.sh <submission.tar.gz-or-run-dir>
```

## Notes

- Solver-facing `task_env/` contains only `executable`, `compile.sh`, and docs.
- Janet is committed as a compact attempt record rather than the final selected
  take-home task.
