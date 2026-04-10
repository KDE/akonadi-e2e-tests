<!--
SPDX-FileCopyrightText: Daniel Vrátil <dvratil@kde.org>

SPDX-License-Identifier: GPL-2.0-or-later
-->

# Akonadi E2E Tests

A [pytest][pytest]-based test suite for end-to-end testing of Akonadi Resources
against real servers.

Akonadi itself has a fairly exhaustive test-suite that performs various operations against
a fully running Akonadi server. However, those tests only cover interaction with Akonadi itself
and only use a special testing Akonadi Resource (the `akonadi_knut_resource`).

Individual Akonadi Resources (like the IMAP Resource, or Google Groupware Resource) have a
very limited subset of unit-tests, but there are no tests that would verify the interaction
of the resource implementation with both Akonadi and the backend service. This is what this
project aims to change.

This repository contains code to start an isolated instance of Akonadi, set up various Akonadi
Resources from [kdepim-runtime][kdepim-runtime], set up a Cyrus IMAP server in various configurations
and more. All that is done through [pytest fixtures][pytest-fixtures] to ensure proper setup
and teardown.

## Running

This project uses the [`uv`][uv] Python project manager.


This project also use akonadiCore python bindings created with the ECMGeneratePythonBindings module.
For now, the bindings must be installed on your system for the tests to work properly.

**Create the virtual environment**
```shell
uv venv --system-site-packages
```

**Add your bindings paths to pyproject**
For your project to have access to python bindings, you must add the path of the `.so` bindings file to your `PYTHONPATH`, or edit the `pyproject.toml` file like this :
```toml
pythonpath = ["src", {bindings_path}]
```

**Install dependencies**
```shell
uv sync
```

**Run all tests including lints (any additional arguments will be passed to `pytest`)**:

```shell
uv run pytest
```

Optionally, pass `-n <number>` to run `<number>` tests in parallel (using `pytest-xdist`).

To see debug output from Akonadi and the test itself, pass `--log-cli-level=debug`.

**Add new dependency**
```shell
uv add <package>
```

For further usage, see the [`uv` documentation][uv].

## Debuging

To help debug failures, you can add your own qt logging rules and message patterns by adding the following lines in the `environ` method in the `src/akonadi/env.py` file :

```python
env["QT_LOGGING_RULES"] = ("{your logging rules}")
env["QT_MESSAGE_PATTERN"] = "{message pattern}"
```


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



[kdepim-runtime]: https://invent.kde.org/pim/kdepim-runtime
[pytest]: https://pytest.org
[pytest-fixtures]: https://docs.pytest.org/en/7.1.x/how-to/fixtures.html
[uv]: https://docs.astral.sh/uv/
[pep-8]: https://peps.python.org/pep-0008/
[pep-257]: https://peps.python.org/pep-0257/
[ruff]: https://docs.astral.sh/ruff/
[mypy]: https://www.mypy-lang.org/
