# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later
import locale
import os
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import pytest
from imap_tools import BaseMailBox, MailBoxUnencrypted
from PySide6.QtCore import QCoreApplication  # type: ignore

from src.akonadi.client import AkonadiClient
from src.akonadi.dav_resource import DAVResource
from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.env import AkonadiEnv
from src.akonadi.imap_resource import ImapResource
from src.akonadi.server import AkonadiServer
from src.dav.client import DavClient
from src.dav.dav_server import DAVServer, DAVServerType
from src.dav.nextcloud_server import NextCloudServer
from src.dav.radicale_server import RadicaleServer
from src.imap.cyrus_server import CyrusServer
from src.imap.dovecot_server import DovecotServer
from src.imap.imap_server import ImapServer, ImapServerType


@pytest.fixture(autouse=True)
def fix_locale():
    """
    Sets the locale to 'C' to ensure consistent behavior across different systems
    LC_TIME is used for date from RFC 822 that use month names abbr. in English
    """
    locale.setlocale(locale.LC_ALL, "C")


@pytest.fixture(scope="session")
def instance_id() -> Generator[str, Any]:
    """Pytest fixture that creates a temporary directory for an Akonadi instance.

    Returns:
        The instance ID of the Akonadi instance.
    """
    with tempfile.TemporaryDirectory(prefix="akonadi-e2e-", delete=False) as tempdir:
        yield Path(tempdir).name


@pytest.fixture(scope="session")
async def dbus_client(instance_id: str) -> AsyncGenerator[AkonadiDBus]:
    """A pytest fixture that creates a new AkonadiDBus client.

    Depends on the `instance_id` fixture.
    """
    dbus = AkonadiDBus(instance_id)
    yield dbus
    dbus.close()


@pytest.fixture(scope="session")
def _akonadi_env(instance_id: str) -> Generator[AkonadiEnv, Any]:
    tempdir = Path(os.environ.get("TMPDIR", "/tmp")) / instance_id
    env = AkonadiEnv(tempdir, instance_id)
    os.environ.update(env.environ)
    yield env


@pytest.fixture(scope="session")
def akonadi_server(_akonadi_env: AkonadiEnv) -> Generator[AkonadiServer]:
    """Pytest fixture that creates an Akonadi server.

    Returns:
        The Akonadi server.
    """
    server = AkonadiServer(_akonadi_env)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope="session", autouse=True)
def qcore_app(_akonadi_env: AkonadiEnv):
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    yield app


@pytest.fixture(scope="session", params=list(DAVServerType))
async def dav_server(request: pytest.FixtureRequest) -> AsyncGenerator[DAVServer]:
    server_type = request.param
    match server_type:
        case DAVServerType.NEXTCLOUD:
            server = NextCloudServer()
        case DAVServerType.RADICALE:
            server = RadicaleServer()
        case _:
            pytest.fail(f"Unknown DAV server type: {dav_server}")

    await server.start()
    yield server
    await server.stop()


@pytest.fixture(scope="session", params=list(ImapServerType))
def server_type(request):
    return request.param


@pytest.fixture(scope="session")
def imap_server_session(server_type: ImapServerType) -> Generator[ImapServer]:
    match server_type:
        case ImapServerType.CYRUS:
            server = CyrusServer()
        case ImapServerType.DOVECOT:
            server = DovecotServer()
        case _:
            pytest.fail(f"Unknown IMAP server type: {server_type}")

    server.start()

    yield server
    server.stop()


@pytest.fixture
def imap_server(imap_server_session: ImapServer) -> Generator[ImapServer]:
    imap_server_session.prepare_test_environment()

    yield imap_server_session

    imap_server_session.cleanup_test_environment()


@pytest.fixture()
def akonadi_client(
    akonadi_server: AkonadiServer,
) -> Generator[AkonadiClient]:
    client = AkonadiClient(akonadi_server.env)
    yield client


@pytest.fixture()
async def imap_resource(
    akonadi_client: AkonadiClient,
    dbus_client: AkonadiDBus,
    imap_server: ImapServer,
) -> AsyncGenerator[ImapResource]:
    resource = ImapResource.create(akonadi_client, dbus_client)
    await resource.configure(
        host=imap_server.host_or_ip,
        port=imap_server.port,
        username=imap_server.username,
        password=imap_server.password,
    )
    resource.synchronize()
    yield resource

    # Remove the resource after the test - this cleans up useless secrets from the keychain
    await resource.remove()


@pytest.fixture()
def imap_client(
    imap_server: ImapServer,
) -> Generator[BaseMailBox]:
    mailbox = MailBoxUnencrypted(imap_server.host_or_ip, imap_server.port)
    mailbox.login(imap_server.username, imap_server.password)
    yield mailbox
    mailbox.logout()


@pytest.fixture()
async def dav_client(dav_server: DAVServer) -> AsyncGenerator[DavClient]:
    client = DavClient(dav_server.base_url, dav_server.username, dav_server.password)
    yield client


@pytest.fixture()
async def groupware_resource(
    akonadi_client: AkonadiClient, dbus_client: AkonadiDBus, dav_server: DAVServer
) -> AsyncGenerator[DAVResource]:
    resource = DAVResource.create(akonadi_client, dbus_client)
    await resource.configure(
        dav_server.base_url, username=dav_server.username, password=dav_server.password
    )
    resource.synchronize()

    yield resource

    await resource.remove()
