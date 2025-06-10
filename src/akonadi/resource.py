# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from abc import abstractmethod
from logging import getLogger
import os

import pytest
from typing_extensions import ClassVar, Self

from src.akonadi.client import AkonadiClient, Collection, Item
from src.akonadi.dbus.client import AkonadiDBus

log = getLogger(__name__)


class Resource:
    RESOURCE_TYPE: ClassVar[str]

    def __init__(
        self, akonadi_client: AkonadiClient, dbus: AkonadiDBus, instance_id: str
    ) -> None:
        self._dbus = dbus
        self._instance_id = instance_id
        self._akonadi_client = akonadi_client

    @classmethod
    async def create(cls, akonadi_client: AkonadiClient, dbus: AkonadiDBus) -> Self:
        log.debug("Creating %s resource via D-Bus", cls.RESOURCE_TYPE)
        instance_id = await dbus.agent_manager_interface.create_agent_instance(
            cls.RESOURCE_TYPE
        )

        timeout = None if os.environ.get("AKONADI_DEBUG_WAIT", None) else 10
        await dbus.wait_for_service(dbus.agent_service_name(instance_id), timeout)

        return cls(akonadi_client, dbus, instance_id)

    async def remove(self) -> None:
        log.debug("Removing %s resource via D-Bus", self.RESOURCE_TYPE)
        await self._dbus.agent_manager_interface.remove_agent_instance(
            self._instance_id
        )

        # Give time to shut down the resource fully
        await asyncio.sleep(0.5)


    @abstractmethod
    async def configure(
        self, host: str, port: int, username: str, password: str
    ) -> None: ...

    async def synchronize(self) -> None:
        log.debug("Synchronizing %s resource via D-Bus", self.RESOURCE_TYPE)
        resource = self._dbus.resource_interface(self._instance_id)
        await resource.synchronize_collection_tree()
        await anext(resource.collection_tree_synchronized.catch())

        await resource.synchronize()
        await anext(resource.synchronized.catch())
        log.debug("%s resource synchronized", self.RESOURCE_TYPE)

    @property
    def instance_id(self) -> str:
        return self._instance_id

    async def resolve_collection(self, collection_name: str) -> Collection:
        path = collection_name.split("/")

        collections = await self._akonadi_client.list_collections(
            parent_id=0, first_level=True
        )
        resource_root = next(
            filter(lambda c: c.resource == self.instance_id, collections), None
        )
        if not resource_root:
            pytest.fail("Resource root collection not found")

        async def resolve_recursive(parent: Collection, path: list[str]):
            if not path:
                return parent

            collections = await self._akonadi_client.list_collections(
                parent_id=parent.id, first_level=True
            )
            collection = next(filter(lambda c: c.name == path[0], collections), None)
            if not collection:
                pytest.fail(
                    f"Collection {collection_name} not found: {path[0]} does not exist!"
                )

            return await resolve_recursive(collection, path[1:])

        return await resolve_recursive(resource_root, path)

    async def sync_collection(self, collection_name: str) -> None:
        collection = await self.resolve_collection(collection_name)
        await self._dbus.resource_interface(self._instance_id).synchronize_collection(
            collection.id, recursive=False
        )

    async def list_collections(self) -> list[Collection]:
        collections = await self._akonadi_client.list_collections(
            parent_id=0, first_level=True
        )
        resource_root = next(
            filter(lambda c: c.resource == self.instance_id, collections), None
        )
        if not resource_root:
            pytest.fail("Resource root collection not found")

        return await self._akonadi_client.list_collections(parent_id=resource_root.id)

    async def list_items(self, collection_name_or_id: str | int) -> list[Item]:
        if isinstance(collection_name_or_id, str):
            collection = await self.resolve_collection(collection_name_or_id)
            if not collection:
                pytest.fail(f"Collection {collection_name_or_id} not found")

            collection_id = collection.id
        else:
            collection_id = int(collection_name_or_id)

        return await self._akonadi_client.list_items(collection_id=collection_id)
