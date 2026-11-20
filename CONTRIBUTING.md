# Contributing to ModelFit

Thanks for helping make local AI easier to use.

## Getting started

1. Open an Issue before a substantial feature or behavioral change.
2. Fork https://github.com/Dhruvkp07/ModelFit and create a descriptive branch.
3. Clone your fork and install Python 3.10+.
4. Install development dependencies and run tests:

~~~bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m modelfit recommend
~~~

5. Include tests and explain changes clearly in your Pull Request.
6. Keep docs/PROJECT_STATE.md and docs/ARCHITECTURE.md accurate for changes affecting architecture.
7. Model metadata changes need a direct primary-source URL.

## Small contributions welcome
Documentation and Windows compatibility fixes, deterministic hardware probe tests, clearer error messages, small model records, and accessibility improvements are welcome.

## Pull request rules
- Keep each PR focused and easy to review.
- Never upload a user's machine fingerprint, personal files, secrets, or API keys.
- Avoid unnecessary dependencies and internet calls; default behavior must remain offline.
- Do not claim models are guaranteed to work or that speed is known without benchmarks.
- A maintainer reviews and merges changes; public access does not grant direct write permissions.

Please be respectful when reviewing others' contributions. See CODE_OF_CONDUCT.md.
