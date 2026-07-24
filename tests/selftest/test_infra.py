# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from AkonadiCore import Akonadi  # type: ignore
from imap_tools import MailBoxUnencrypted

from src.akonadi.client import AkonadiClient
from src.akonadi.dav_resource import DAVResource
from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.imap_resource import ImapResource
from src.akonadi.server import AkonadiServer
from src.imap.imap_server import ImapServer
from src.kunifiedpush.kunifiedpush_service import KunifiedPushService
from src.ntfy.ntfy_server import NtfyServer

log = getLogger(__name__)


def test_imap_ready(imap_server: ImapServer):
    client = MailBoxUnencrypted(imap_server.host_or_ip, imap_server.port)
    client.login("admin", "admin")
    client.logout()


def test_akonadi_server_starts(akonadi_server: AkonadiServer, dbus_client: AkonadiDBus) -> None:
    assert akonadi_server.is_running()
    path = dbus_client.server_interface.server_path()
    assert path.startswith("/tmp/akonadi-e2e-")


def test_akonadi_client_list_collections(akonadi_client: AkonadiClient) -> None:
    collections = akonadi_client.list_collections()
    assert len(collections) == 2
    assert collections[0].id() == 0  # root collection
    assert collections[1].id() == 1  # search collection
    assert collections[1].name() == "Search"


def test_akonadi_client_list_agents(
    akonadi_client: AkonadiClient, imap_resource: ImapResource
) -> None:
    assert imap_resource.identifier.startswith("akonadi_imap_resource_")
    agents = akonadi_client.list_agents()
    assert len(agents) == 1
    assert agents[0].identifier().startswith("akonadi_imap_resource_")
    assert agents[0].name() == "IMAP Account"
    assert agents[0].status() == Akonadi.AgentInstance.Idle
    assert agents[0].type().identifier() == "akonadi_imap_resource"


def test_akonadi_imap_resource(imap_resource: ImapResource) -> None:
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


def test_akonadi_client_list_agents_dav_push_notifications(
    akonadi_client: AkonadiClient, groupware_push_notifications_resource: DAVResource
) -> None:
    assert groupware_push_notifications_resource.identifier.startswith(
        "akonadi_davgroupware_resource_"
    )
    agents = akonadi_client.list_agents()
    assert len(agents) == 1
    assert agents[0].identifier().startswith("akonadi_davgroupware_resource_")
    assert agents[0].name().startswith(f"akonadi-e2e-test - {akonadi_client.akonadi_instance_name}")
    assert agents[0].status() == Akonadi.AgentInstance.Idle
    assert agents[0].type().identifier() == "akonadi_davgroupware_resource"


def test_capabilities(imap_resource: ImapResource) -> None:
    capabilities = set(imap_resource.call_capabilities())
    if "IMAP4REV2" in capabilities:
        assert all(
            capability in capabilities
            for capability in [
                "NAMESPACE",
                "UNSELECT",
                "UIDPLUS",
                "ESEARCH",
                "SEARCHRES",
                "ENABLE",
                "IDLE",
                "SASL-IR",
                "LIST-EXTENDED",
                "LIST-STATUS",
                "MOVE",
            ]
        )
        assert "LITERAL-" in capabilities or "LITERAL+" in capabilities


def test_ntfy_server(ntfy_server: NtfyServer):
    """
    Publishes and reads a new message on the default test topic
    """
    ntfy_server.send_message("test message")

    messages = ntfy_server.get_messages()
    assert len(messages) == 1
    assert messages[0]["message"] == "test message"


def test_kunifiedpush_healthy(kunifiedpush_service: KunifiedPushService):
    """
    Check that kunifiedpush is ready and healthy, by registering and unregistering to a test topic
    """
    token = "health_check_topic"

    previous_registers = kunifiedpush_service.registered_clients()

    result_register = kunifiedpush_service.register(token)
    assert result_register["success"] == ("s", "REGISTRATION_SUCCEEDED")

    current_registers = kunifiedpush_service.registered_clients()
    assert len(current_registers) == len(previous_registers) + 1

    result_unregister = kunifiedpush_service.unregister(token)
    assert len(result_unregister) == 0

    current_registers = kunifiedpush_service.registered_clients()
    assert len(current_registers) == len(previous_registers)
