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

## Running the tests

This project uses the [`uv`][uv] Python project manager, and test containers to launch its test servers images. By default, python's [`testcontainers`][testcontainers] creates a priviledged `ryuk` container to manage other container's life cycles. If you do not want to launch ryuk, or get a `permission denied` error from docker when trying to launch the tests, set `TESTCONTAINERS_RYUK_DISABLED` to `true` in your environment (more information [`here`][testcontainers]).


This project also use akonadiCore python bindings created with the ECMGeneratePythonBindings module.
For now, the bindings must be installed on your system for the tests to work properly.

**Build the required docker images**
```shell
make docker
```

**Create the virtual environment and install dependencies**
```shell
make init
```

**Run all tests including lints**:

```shell
make test
```

**Run only linting / type checking tests**:

```shell
make lint
```

Optionally, you can directly use uv + pytest to run the tests :
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

## Tests basics

Most of the tests in this repo test the behaviour of an akonadi IMAP or DAV resource during various operations, as well as the synchronization of said resource with the configured IMAP / DAV server.

This repo uses pytest fixtures, as well as [FactoryBoy][factory-boy] factories to setup and teardown anything needed for the tests.

### Repo Structure

#### The `/src` folder

Contains classes used to initialise and interact with the different test fixtures (test servers, clients factories...) :

* `/src/akonadi` : contains the classes used to setup and interact with the akonadi server, the akonadi client and the akonadi resources, as well as some utils method to wait for some particular akonadi signals.

* `/src/imap` and `/src/dav` : contains the classes used to launch the IMAP and DAV servers images used by the tests, as well as some utils methods to communicate better with those servers. You can find the dockerfile of the docker images in the `/docker` folder

* `/src/factories` : contains the differents FactoryBoy factories used to setup test data in akonadi or in the server at the beginning of each test.

#### The `/tests` folder

The tests are separated into different folders depending on the tested resource (ex: `/tests/imap` for imap resource tests), in addition to the `tests/selftest` folder, used to test our test servers, fixtures, factories... are working fine.

Inside each folder, the tests are organized as so :
* `test_generic` : test base state and generic operations like list the initial sync or listing elements
* `test_resource_to_server` : test cases where we make operations on the akonadi resource (for example by adding an item or a collection) and check if the change is correctly repercuted on the server
* `test_server_to_resource` : test cases where we make operations on the server (modyfying a calendar, a mailbox...) and check if the change is correctly repercuted on the akonadi server.
* `test_conflicts` : tests cases where we make different changes in both the akonadi resource and the element on the server (for example, deleting a collection in the server, but creating an item in this collection in akonadi) while they are disconnected (the resource is set to offline), then we reconnect them (set the resource back to online) and check for the expected behaviour.

### Resource and server synchronization

Once you made changes to the resource or the server, we need to make sure the changes have been applied on the other side :

* If you made changes on the server, you can call the `synchronize` method of the resource to apply the changes on akonadi's side. You can also call `sync_collection` if you do not need a full sync of all the collections in the server.
* If you made changes on akonadi's side, you will have to call `wait_until`, and specify the condition you want to wait for (ex: a new mailbox existing in the server).

### Online and offline resource

During the tests, the tested resource is set online by default, and can be set offline manually.

If the resource is online, most changes to the resource or in the server will immediately be synced between the two.

If the resource is set offline, the changes made to either of the two can only be synced when the resource is set back online.

You can change the state of a resource with the `setOnline` method of the `Resource` class.

Be careful, **with the IMAP resource only, putting the resource back online will only trigger a collection tree synchronization** (collections will be synced, but not the items in them on Akonadi's side). To trigger a full sync, you will have to call `synchronize` manually after setting the resource online. With the DAV resource, a full sync is triggered by default when setting the resource online.

### iTYPE calendar selection popup

When receiving an iType invitation, if you have more than one calendar, a popup asking you to select the calendar in which to accept the invitation will appear, which will block the test.

Since this popup cannot be deactivated, it is heavily recommended to not have more calendars than the default one, when testing iType invitations.

## Guidelines for writing new tests

Here are some rules and tips if you want to write some new tests :
* Place your tests in the right file(s), depending on the resource type and [test case](#the-tests-folder).
* Give your tests a meaniful name, describing precisely what is tested, and if the tested resource is in an online or offline state during the tested operations.
* Write a short docstring explaining more in detail what the test does, and the expected behavior.
* Whenever possible, try to use the factories for the setup of your tests.
* Don't forget to ensure than the state of the items / collections are coherent between akonadi and the server.

### Frequent mistakes

* When changing attributes of a collection (for example a dav collection's color), you should only supply values for attributes to be updated. More information [here][collection-modify-job].

## Debuging tools

### Logs

To help debug failures, you can add your own qt logging rules and message patterns by adding the following lines in the `environ` method in the `src/akonadi/env.py` file :

```python
env["QT_LOGGING_RULES"] = ("{your logging rules}")
env["QT_MESSAGE_PATTERN"] = "{message pattern}"
```

Logs from the different test servers are forwarded to journnald, with a specific tag for each server. You can access them with :
```shell
journalctl CONTAINER_TAG={server-type}-akonadi-e2e-tests
```
For example, `journalctl CONTAINER_TAG=dovecot-akonadi-e2e-tests` to access dovecot server logs.

### AkonadiConsole

AkonadiConsole can be useful for debuging, as it allows to see the different resource configurations, jobs, etc... However, to open AkonadiConsole on the AkonadiServer created by the tests, you need to set a environment variable that change each test session, depending on the akonadiserver id.

To help with that, a `akonadiconsole.sh` file is created at the begining of each test session. You just have to exec this file while the tests are running to launch akonadiconsole (ignore the error popups concerning the database at startup).

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
[factory-boy]: https://factoryboy.readthedocs.io/en/stable/
[collection-modify-job]: https://invent.kde.org/pim/akonadi/-/blob/master/src/core/jobs/collectionmodifyjob.h?ref_type=heads#L34-L39
[testcontainers]: https://testcontainers-python.readthedocs.io/en/latest/
