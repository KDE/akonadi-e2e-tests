<!--
SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>

SPDX-License-Identifier: GPL-2.0-or-later
-->

# Akonadi E2E Tests

A [pytest][pytest]-based test suite for end-to-end testing of Akonadi Resources
against various real servers.

Akonadi itself has a fairly exhaustive test-suite that performs various operations against
a fully running Akonadi server. However, those tests only cover interaction with Akonadi itself
and only use a special testing Akonadi Resource (the akonadi_knut_resource).

Individual Akonadi Resources (like the IMAP Resource, or Google Groupware Resource) have a
very limited subset of unit-tests, but there are no tests that would verify the interaction
of the resource implementation with both Akonadi and the backend service. This is what this
project aims to change.

This repository contains code to start an isolated instance of Akonadi, set up various Akonadi
Resources from [kdepim-runtime][kdepim-runtime], set up a Cyrus IMAP server in various configurations
and more. All that is done through [pytest fixtures][pytest-fixtures] to ensure proper setup
and teardown.

## Running

## Conventions

This project uses modern Python with full type hints, and follows [PEP-8][pep-8] and [PEP-257][pep-257],
with some modern deviations (e.g. maximum line length is 100 instead of 79), mostly the [`ruff`][ruff]
defaults.

To enforce code formatting and passing lints, we use the following tools:

* [`ruff`][ruff] for code-formatting an linting
* [`mypy`][mypy] for type checking

You can enable [pre-commit hook](https://pre-commit.com) by installing `pre-commit` and running

```
pre-commit install
```

in this respository. This will automatically run all linters on each commit.



[pytest]: https://pytest.org
[pytest-fixtures]: https://docs.pytest.org/en/7.1.x/how-to/fixtures.html
[pep-8]: https://peps.python.org/pep-0008/
[pep-257]: https://peps.python.org/pep-0257/
[ruff]: https://docs.astral.sh/ruff/
[mypy]: https://www.mypy-lang.org/
