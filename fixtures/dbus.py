# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
This module contains a high-level client for the Akonadi DBus service.
and a Pytest fixture to create the client.
"""

import asyncio
from logging import getLogger
from typing import AsyncGenerator
from dbus_next.aio import MessageBus
from dbus_next.aio.proxy_object import ProxyInterface
from dbus_next.message import Message
import pytest

log = getLogger(__name__)

class AkonadiDBus:
    """A high-level client for the Akonadi DBus service."""

    def __init__(self, instance_id: str, client: MessageBus) -> None:
        self._instance_id = instance_id
        self._client = client

    @classmethod
    async def create(cls, instance_id: str) -> 'AkonadiDBus':
        client = await MessageBus().connect()

        return AkonadiDBus(instance_id, client)

    async def disconnect(self) -> None:
        self._client.disconnect()
        await self._client.wait_for_disconnect()

    async def wait_for_service(
        self, service_name: str, timeout_secs: float = 10
    ) -> None:
        await asyncio.wait_for(
            self._wait_for_name_owner(service_name),
            timeout=timeout_secs,
        )

    @property
    def akonadi_server_service_name(self) -> str:
        return f"org.freedesktop.Akonadi.{self._instance_id}"

    @property
    def akonadi_control_service_name(self) -> str:
        return f"org.freedesktop.Akonadi.Control.{self._instance_id}"

    async def server_interface(self) -> ProxyInterface:
        introspection = await self._client.introspect(
            self.akonadi_server_service_name,
            "/Server",
        )
        server_object = self._client.get_proxy_object(
            self.akonadi_server_service_name,
            "/Server",
            introspection,
        )

        return server_object.get_interface("org.freedesktop.Akonadi.Server")

    async def control_interface(self) -> ProxyInterface:
        introspection = await self._client.introspect(
            self.akonadi_control_service_name,
            "/ControlManager",
        )
        control_object = self._client.get_proxy_object(
            self.akonadi_control_service_name,
            "/ControlManager",
            introspection,
        )

        return control_object.get_interface("org.freedesktop.Akonadi.ControlManager")

    async def _wait_for_name_owner(self, service_name: str) -> None:
        introspection = await self._client.introspect(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
        )
        proxy = self._client.get_proxy_object(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            introspection,
        )

        interface = proxy.get_interface("org.freedesktop.DBus")
        event = asyncio.Event()

        def name_owner_changed(name: str, _old_owner: str, new_owner: str) -> None:
            if name == service_name:
                log.debug("Name owner changed: %s -> %s", name, new_owner)
                event.set()

        interface.on_name_owner_changed(name_owner_changed) # type: ignore[attr-defined]

        resp = await self._client.call(
            Message(
                destination="org.freedesktop.DBus",
                path="/org/freedesktop/DBus",
                interface="org.freedesktop.DBus",
                member="GetNameOwner",
                signature="s",
                body=[service_name],
            )
        )
        if not resp or resp.error_name == "org.freedesktop.DBus.Error.NameHasNoOwner":
            log.debug("Service %s has no owner, waiting for it...", service_name)
            await event.wait()
        else:
            log.debug("Service %s has owner %s, continuing", service_name, resp.body[0])


@pytest.fixture()
async def dbus_client(instance_id: str) -> AsyncGenerator[AkonadiDBus, None]:
    """A pytest fixture that creates a new AkonadiDBus client.

    Depends on the `instance_id` fixture.
    """
    dbus = await AkonadiDBus.create(instance_id)
    yield dbus
    await dbus.disconnect()
