# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
from typing import AsyncGenerator
import tempfile
import pytest

from src.dav.dav_server import DAVServerType, DAVServer
from src.imap.imap_server import ImapServer, ImapServerType
from src.akonadi.dav_resource import DAVResource
from src.akonadi.server import AkonadiServer
from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.akonadi.dbus.client import AkonadiDBus
from src.imap.client import ImapClient
from src.imap.cyrus_server import CyrusServer
from src.dav.nextcloud_server import NextCloudServer
from src.dav.client import DavClient


@pytest.fixture()
async def instance_id() -> AsyncGenerator[str, None]:
    """Pytest fixture that creates a temporary directory for an Akonadi instance.

    Returns:
        The instance ID of the Akonadi instance.
    """
    with tempfile.TemporaryDirectory(prefix="akonadi-e2e-", delete=False) as tempdir:
        yield Path(tempdir).name


@pytest.fixture()
async def dbus_client(instance_id: str) -> AsyncGenerator[AkonadiDBus, None]:
    """A pytest fixture that creates a new AkonadiDBus client.

    Depends on the `instance_id` fixture.
    """
    dbus = AkonadiDBus(instance_id)
    yield dbus
    dbus.close()


@pytest.fixture()
@pytest.mark.parametrize("server_type", [ImapServerType.CYRUS])
async def imap_server(
    request: pytest.FixtureRequest, instance_id: str, server_type: ImapServerType
) -> AsyncGenerator[ImapServer, None]:
    match server_type:
        case ImapServerType.CYRUS:
            server = CyrusServer(Path(f"/tmp/{instance_id}"))
            if param := getattr(request, "param", None):
                assert isinstance(param, dict), (
                    "imap_server fixture parameters must be a dictionary"
                )
                for key, value in param.items():
                    match key:
                        case "suppress_capabilities":
                            server.suppress_capabilities(value)
                        case _:
                            raise ValueError(f"Unknown imap_server parameter: {key}")
        case _:
            pytest.fail(f"Unknown IMAP server type: {server_type}")

    await server.start()
    await server.prepare_test_environment()

    yield server
    await server.stop()


@pytest.fixture()
async def akonadi_server(
    instance_id: str, dbus_client: AkonadiDBus
) -> AsyncGenerator[AkonadiServer, None]:
    """Pytest fixture that creates an Akonadi server.

    Returns:
        The Akonadi server.
    """

    server = AkonadiServer(instance_id, dbus_client)
    await server.start()
    yield server
    await server.stop()


@pytest.fixture()
async def akonadi_client(
    akonadi_server: AkonadiServer,
) -> AsyncGenerator[AkonadiClient, None]:
    client = AkonadiClient(akonadi_server.env)
    yield client


@pytest.fixture()
async def imap_resource(
    akonadi_client: AkonadiClient,
    dbus_client: AkonadiDBus,
    imap_server: ImapServer,
) -> AsyncGenerator[ImapResource, None]:
    resource = await ImapResource.create(akonadi_client, dbus_client)
    await resource.configure(
        host=imap_server.host_or_ip,
        port=imap_server.port,
        username=imap_server.username,
        password=imap_server.password,
    )
    await resource.synchronize()
    yield resource

    # Remove the resource after the test - this cleans up useless secrets from the keychain
    await resource.remove()


@pytest.fixture()
async def imap_client(
    imap_server: ImapServer,
) -> AsyncGenerator[ImapClient, None]:
    client = ImapClient(imap_server.host_or_ip, imap_server.port)
    await client.connect(imap_server.username, imap_server.password)
    yield client
    await client.disconnect()


@pytest.fixture()
@pytest.mark.parametrize("server_type", [DAVServerType.NEXTCLOUD])
async def dav_server(server_type: DAVServerType) -> AsyncGenerator[DAVServer, None]:
    match server_type:
        case DAVServerType.NEXTCLOUD:
            server = NextCloudServer()
        case _:
            pytest.fail(f"Unknown DAV server type: {dav_server}")

    await server.start()
    yield server
    await server.stop()


@pytest.fixture()
async def dav_client(dav_server: DAVServer) -> AsyncGenerator[DavClient, None]:
    client = DavClient(dav_server.base_url, dav_server.username, dav_server.password)
    yield client


@pytest.fixture()
async def groupware_resource(
    akonadi_client: AkonadiClient,
    dbus_client: AkonadiDBus,
    dav_server: DAVServer,
) -> AsyncGenerator[DAVResource, None]:
    resource = await DAVResource.create(akonadi_client, dbus_client)
    await resource.configure(
        dav_server.base_url, username=dav_server.username, password=dav_server.password
    )
    await resource.synchronize()

    yield resource

    await resource.remove()
