# FSRS-6 implementation audit

紫藤学习系统使用的是浏览器原生 JavaScript 实现的 FSRS-6 本地移植版。它不是固定的 1/3/7/30 天阶梯，也没有把个人猜测写进长期复习间隔。

## Reference pin

- Long-term memory model: public `FSRS-6` formulas and 21 default weights
- Cross-check implementation: `open-spaced-repetition/ts-fsrs` 5.4.1
- Learning/relearning transitions: current Anki manual rules
- Default requested retention: `0.90`
- Default maximum interval: `36500` days
- Default learning steps: `1m, 10m`
- Default relearning step: `10m`
- Fuzz: disabled by default
- Short-term stability: enabled

## Audited model surface

The local implementation is checked against the public FSRS-6 model surface for:

- the 21 default weights;
- decay and factor calculation;
- forgetting curve and interval conversion;
- initial stability and difficulty;
- difficulty update and mean reversion;
- successful-recall stability;
- forgotten-card stability and the short-term upper bound;
- same-day short-term stability, including Hard not shrinking stability;
- New, Learning, Review and Relearning transitions;
- learning and relearning steps;
- calendar-day elapsed-time handling;
- interval ordering for Hard, Good and Easy;
- lapse and repetition counters.

## Test coverage

`tests/fsrs.test.js` includes deterministic invariants, state-transition checks and 32,000 randomized review events. It rejects NaN, invalid states, impossible dates, out-of-range difficulty, non-positive stability and incorrectly ordered intervals.

## Deliberate boundaries

- The web application itself does not train personal parameters. An optional command-line tool using the official FSRS binding is included in `tools/optimize_fsrs.mjs`; until it is run on a sufficiently large personal review history, the application keeps the default weights.
- Fuzz exists but is disabled by default so test output and predicted intervals remain deterministic.
- Learning-step behavior is controlled separately from long-term FSRS intervals, as in Anki-style workflows.
- This audit does not claim that a third-party local port can never contain a defect. It makes the implementation inspectable, pinned and regression-tested instead of opaque.
