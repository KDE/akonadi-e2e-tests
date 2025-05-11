# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
from typing import AsyncGenerator
import tempfile
import pytest

from src.akonadi import AkonadiDBus, AkonadiServer, AkonadiClient
from src.imap.cyrus_server import CyrusServer


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
    dbus = await AkonadiDBus.create(instance_id)
    yield dbus
    await dbus.disconnect()


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


@pytest.fixture
async def cyrus_server(instance_id: str) -> AsyncGenerator[CyrusServer, None]:
    server = CyrusServer(Path(f"/tmp/{instance_id}"))
    await server.start()
    yield server
    await server.stop()
