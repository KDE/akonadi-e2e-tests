# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Meta-tests that check that the infrastructure for the tests is working as expected.
"""

from aioimaplib import aioimaplib  # type: ignore
import pytest

from src.akonadi import AkonadiServer, AkonadiDBus, AkonadiClient
from src.imap import CyrusServer


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
    iface = await dbus_client.server_interface()
    path: str = await iface.call_server_path()  # type: ignore[attr-defined]
    assert path.startswith("/tmp/akonadi-e2e-")


@pytest.mark.asyncio
async def test_akonadi_client(akonadi_client: AkonadiClient) -> None:
    collections = await akonadi_client.list_collections()
    assert len(collections) == 2
    assert collections[0].id == 0  # root collection
    assert collections[1].id == 1  # search collection
    assert collections[1].name == "Search"
