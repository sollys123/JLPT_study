# Test report

Build: 4.1.0  
Date: 2026-08-03

## Automated checks

Run from the repository root:

```bash
node tests/fsrs.test.js
node tests/dictionary.test.js
python tests/static_app_test.py
python tests/browser_test.py
```

Validated areas:

- 336 unique plan dates from 2026-08-03 to 2027-07-04;
- France travel mode from 2026-09-29 to 2026-10-08;
- lesson 29 resuming on 2026-10-12;
- no travel-day backlog pollution;
- FSRS-6 mathematical invariants and state transitions;
- 32,000 randomized FSRS review events;
- current jmdict-simplified example-object parsing;
- dictionary lookup, note creation and five sibling card templates;
- card review, review history, diagnostics and JSON backup;
- desktop and 390px mobile layout;
- static asset references, service-worker shell and deployment file set.

## Environment boundary

The execution sandbox blocks navigation to localhost and custom test origins. Therefore the browser regression suite injects the application into an isolated page and uses an in-memory IndexedDB-compatible adapter. The shipped application still uses the native IndexedDB implementation in `assets/js/db.js`, and the in-app diagnostic performs a real write/read/delete round trip in the user’s browser.

GitHub Actions additionally runs deterministic tests before deployment and stops the release if a test or JMdict SHA-256 verification fails.

## Optional optimizer boundary

The optional `tools/optimize_fsrs.mjs` command is not required by the web application or the Pages deployment. Its module API was checked against the upstream `@open-spaced-repetition/binding` 0.5.0 source and its JavaScript syntax is validated locally. The execution sandbox used for this build did not expose that package through its internal npm mirror, so the optimizer itself was not trained here. Run it only after a normal public `npm install` and after accumulating substantial real review history.
