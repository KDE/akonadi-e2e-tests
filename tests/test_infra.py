# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Meta-tests that check that the infrastructure for the tests is working as expected.
"""
from aioimaplib import aioimaplib  # type: ignore

import pytest
from fixtures.akonadi import AkonadiServer
from fixtures.dbus import AkonadiDBus
from fixtures.cyrus import CyrusServer

# Ensure that tests in this module are always run before any other modules, so that we
# can ensure that the infrastructure is working as expected.
testmark = pytest.mark.order(1)

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
    path: str = await dbus_client.server_interface.call_server_path()  # type: ignore[attr-defined]
    assert path.startswith("/tmp/akonadi-e2e-test-")
