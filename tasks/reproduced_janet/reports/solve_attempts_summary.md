# Janet mini-SWE Solve Attempts Summary

This directory records the Janet task recreation attempt that was later set
aside in favor of PocketLang. The Janet pipeline itself was viable: gold build,
harvested/generated tests, coverage, deterministic fairness, LM-as-judge
fairness review, and hardened evaluator checks all passed. The blocker was the
actual lightweight Gemini mini-SWE solve behavior, which repeatedly failed to
produce a useful native reimplementation.

## Task Snapshot

- Repository: `janet-lang/janet`
- Pinned tag: `v1.41.2`
- Pinned commit: `0fea20c82182fe661f75b00a8889d801fe2d79b6`
- Instance ID: `janet-lang__janet.0fea20c`
- Gold SHA256:
  `0803a73d40bcce61c07950d509d023d40ccc896fff3ca57571a4194377678235`
- Generated suite: 381 behavioral pytest tests
- Generated coverage: 75.3% line, 68.5% branch
- Quality gate: gold passed 381/381; dummy passed 0/381
- Deterministic fairness: pass
- LM-as-judge fairness: task/evaluator fairness checks passed; latest inspected
  solve was disqualified by the evaluator for oracle embedding.

## Eval Attempts

| Run | Eval status | Passed | Failed | Notes |
| --- | --- | ---: | ---: | --- |
| `janet_miniswe_20260630_095804` | rejected_wrapper_or_oracle | 0 | 0 | exact oracle bytes detected |
| `janet_miniswe_20260630_104423` | rejected_wrapper_or_oracle | 0 | 0 | exact oracle bytes detected |
| `janet_miniswe_20260630_142119` | rejected_wrapper_or_oracle | 0 | 0 | oracle bytes plus binary-data wrapper patterns detected |
| `janet_miniswe_20260630_202115` | failed | 0 | 381 | non-oracle candidate, no useful behavioral coverage |
| `janet_miniswe_20260701_000424` | failed | 1 | 380 | non-oracle candidate |
| `janet_miniswe_20260701_035506` | failed | 1 | 380 | non-oracle candidate |
| `janet_miniswe_20260701_041230` | failed | 1 | 380 | non-oracle candidate |
| `janet_miniswe_20260701_112513` | failed | 0 | 381 | non-oracle candidate |
| `janet_miniswe_20260701_160140` | failed | 1 | 380 | non-oracle candidate |
| `janet_miniswe_20260701_164959` | failed | 0 | 381 | non-oracle candidate |
| `submission` | failed | 0 | 381 | ad hoc submission eval record |

Only compact `summary.json` records are retained for these attempts. Full
pytest/JUnit logs were omitted from the commit because they duplicate the
summaries and are not needed to understand why Janet was abandoned.

## Outcome

Janet was useful as a stress case for the fairness and anti-cheating scaffold:
it exposed oracle-copying, embedded-binary, parser FormatError, scratchpad,
hardcoded-smoke, and repeated-command failure modes. After those guardrails were
added, the remaining agent attempts still produced near-zero behavioral scores.
The take-home then pivoted to PocketLang, which kept the same task-recreation
pipeline but produced a cleaner final demonstration artifact.
