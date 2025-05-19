# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
from typing import AsyncGenerator
import tempfile
import pytest

from src.akonadi.server import AkonadiServer
from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.akonadi.dbus.client import AkonadiDBus
from src.imap.client import ImapClient
from src.imap.cyrus_server import CyrusServer, prepare_test_environment


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


@pytest.fixture
async def cyrus_server(
    request: pytest.FixtureRequest, instance_id: str
) -> AsyncGenerator[CyrusServer, None]:
    server = CyrusServer(Path(f"/tmp/{instance_id}"))
    if hasattr(request, "param"):
        assert isinstance(request.param, dict), (
            "cyrus_fixture parameters must be a dictionary"
        )
        for key, value in request.param.items():
            match key:
                case "suppress_capabilities":
                    server.suppress_capabilities(value)
                case _:
                    raise ValueError(f"Unknown cyrus_fixture parameter: {key}")

    await server.start()
    yield server
    await server.stop()


@pytest.fixture()
async def cyrus_imap_credentials(
    cyrus_server: CyrusServer,
) -> AsyncGenerator[tuple[str, str], None]:
    username = "test"
    password = "test"

    await prepare_test_environment(username, password, cyrus_server)

    yield (username, password)


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
    request: pytest.FixtureRequest,
    akonadi_client: AkonadiClient,
    dbus_client: AkonadiDBus,
    cyrus_server: CyrusServer,
    cyrus_imap_credentials: tuple[str, str],
) -> AsyncGenerator[ImapResource, None]:
    resource = await ImapResource.create(akonadi_client, dbus_client)
    await resource.configure(
        host="127.0.0.1",
        port=cyrus_server.port,
        username=cyrus_imap_credentials[0],
        password=cyrus_imap_credentials[1],
    )
    await resource.synchronize()
    yield resource
    # We don't really need to do anything here, Akonadi will stop the resource for us


@pytest.fixture()
async def imap_client(
    cyrus_server: CyrusServer,
    cyrus_imap_credentials: tuple[str, str],
) -> AsyncGenerator[ImapClient, None]:
    client = ImapClient("127.0.0.1", cyrus_server.port)
    await client.connect(cyrus_imap_credentials[0], cyrus_imap_credentials[1])
    yield client
    await client.disconnect()
