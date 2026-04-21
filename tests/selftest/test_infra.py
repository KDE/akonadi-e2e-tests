# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

import pytest
from AkonadiCore import Akonadi  # type: ignore
from imap_tools import MailBoxUnencrypted

from src.akonadi.client import AkonadiClient
from src.akonadi.dav_resource import DAVResource
from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.imap_resource import ImapResource
from src.akonadi.server import AkonadiServer
from src.imap.imap_server import ImapServer

log = getLogger(__name__)


@pytest.mark.asyncio
async def test_imap_ready(imap_server: ImapServer):
    client = MailBoxUnencrypted(imap_server.host_or_ip, imap_server.port)
    client.login("admin", "admin")
    client.logout()


@pytest.mark.asyncio
async def test_akonadi_server_starts(
    akonadi_server: AkonadiServer, dbus_client: AkonadiDBus
) -> None:
    assert akonadi_server.is_running()
    path = await dbus_client.server_interface.server_path()
    assert path.startswith("/tmp/akonadi-e2e-")


@pytest.mark.asyncio
async def test_akonadi_client_list_collections(akonadi_client: AkonadiClient) -> None:
    collections = akonadi_client.list_collections()
    assert len(collections) == 2
    assert collections[0].id() == 0  # root collection
    assert collections[1].id() == 1  # search collection
    assert collections[1].name() == "Search"


@pytest.mark.asyncio
async def test_akonadi_client_list_agents(
    akonadi_client: AkonadiClient, imap_resource: ImapResource
) -> None:
    assert imap_resource.identifier.startswith("akonadi_imap_resource_")
    agents = akonadi_client.list_agents()
    assert len(agents) == 1
    assert agents[0].identifier().startswith("akonadi_imap_resource_")
    assert agents[0].name() == "IMAP Account"
    assert agents[0].status() == Akonadi.AgentInstance.Idle
    assert agents[0].type().identifier() == "akonadi_imap_resource"


@pytest.mark.asyncio
async def test_akonadi_imap_resource(imap_resource: ImapResource) -> None:
    assert imap_resource.identifier.startswith("akonadi_imap_resource_")
    collections = imap_resource.list_collections()

    assert len(collections) == 2

    imap_resource.sync_collection("INBOX")
    items = imap_resource.list_items("INBOX")
    assert len(items) == 0


def test_akonadi_dav_resource(groupware_resource: DAVResource) -> None:
    assert groupware_resource.identifier.startswith("akonadi_davgroupware_resource_")
    collections = groupware_resource.list_collections()

    assert len(collections) == 2

    collection = groupware_resource.collection_from_display_name("Default Calendar")
    groupware_resource.sync_collection(collection.remoteId())
    items = groupware_resource.list_items(collection.remoteId())
    assert len(items) == 0


def test_akonadi_client_list_agents_dav(
    akonadi_client: AkonadiClient, groupware_resource: DAVResource
) -> None:
    assert groupware_resource.identifier.startswith("akonadi_davgroupware_resource_")
    agents = akonadi_client.list_agents()
    assert len(agents) == 1
    assert agents[0].identifier().startswith("akonadi_davgroupware_resource_")
    assert agents[0].name().startswith(f"akonadi-e2e-test - {akonadi_client.akonadi_instance_name}")
    assert agents[0].status() == Akonadi.AgentInstance.Idle
    assert agents[0].type().identifier() == "akonadi_davgroupware_resource"
