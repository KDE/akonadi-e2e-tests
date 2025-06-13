# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from aioimaplib import aioimaplib  # type: ignore
import pytest

from src.akonadi.server import AkonadiServer
from src.akonadi.client import AkonadiClient
from src.akonadi.imap_resource import ImapResource
from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.client import AgentStatus
from src.imap import CyrusServer

log = getLogger(__name__)


@pytest.mark.asyncio
async def test_cyrus_ready(cyrus_server: CyrusServer):
    client = aioimaplib.IMAP4(host="127.0.0.1", port=cyrus_server.port, timeout=10.0)
    await client.wait_hello_from_server()
    resp = await client.login("test", "test")
    assert resp.result.startswith("OK")
    await client.logout()


@pytest.mark.asyncio
async def test_akonadi_server_starts(
    akonadi_server: AkonadiServer, dbus_client: AkonadiDBus
) -> None:
    assert await akonadi_server.is_running()
    path = await dbus_client.server_interface.server_path()
    assert path.startswith("/tmp/akonadi-e2e-")


@pytest.mark.asyncio
async def test_akonadi_client_list_collections(akonadi_client: AkonadiClient) -> None:
    collections = await akonadi_client.list_collections()
    assert len(collections) == 2
    assert collections[0].id == 0  # root collection
    assert collections[1].id == 1  # search collection
    assert collections[1].name == "Search"


@pytest.mark.asyncio
async def test_akonadi_client_list_agents(
    akonadi_client: AkonadiClient, imap_resource: ImapResource
) -> None:
    assert imap_resource.identifier == "akonadi_imap_resource_0"
    agents = await akonadi_client.list_agents()
    assert len(agents) == 1
    assert agents[0].identifier == "akonadi_imap_resource_0"
    assert agents[0].name == "IMAP Account"
    assert agents[0].status == AgentStatus.IDLE
    assert agents[0].type == "akonadi_imap_resource"


@pytest.mark.asyncio
async def test_akonadi_imap_resource(imap_resource: ImapResource) -> None:
    assert imap_resource.identifier == "akonadi_imap_resource_0"
    collections = await imap_resource.list_collections()
    assert len(collections) == 6

    await imap_resource.sync_collection("INBOX")
    items = await imap_resource.list_items("INBOX")
    assert len(items) == 2
