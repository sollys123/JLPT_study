# Licences and attribution

## Application code

The application code is released under the MIT License. See `LICENSE`.

## FSRS reference implementation

The local scheduler is an independently packaged browser port audited against the public FSRS-6 formulas and the following reference version:

- Project: `open-spaced-repetition/ts-fsrs`
- Audited version: `5.4.1`
- Licence: MIT
- Repository: https://github.com/open-spaced-repetition/ts-fsrs

The repository’s MIT licence and source documentation govern the upstream cross-check implementation. Review logs record `FSRS-6` together with the application implementation reference for traceability.

## JMdict and jmdict-simplified

JMdict data is not bundled in the source archive. The GitHub Pages workflow can download fixed jmdict-simplified release assets after SHA-256 verification.

JMdict is maintained by the Electronic Dictionary Research and Development Group. Dictionary data and derived packages remain subject to their own licences and attribution requirements, including CC BY-SA 4.0 where applicable.

- EDRDG licence: https://www.edrdg.org/edrdg/licence.html
- JMdict information: https://www.edrdg.org/jmdict/j_jmdict.html
- jmdict-simplified: https://github.com/scriptin/jmdict-simplified

The application stores source identifiers and displays dictionary attribution. Exporting or redistributing installed dictionary data does not change the upstream licence.
