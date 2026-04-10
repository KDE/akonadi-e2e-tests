# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
import os
import time
from logging import getLogger
from typing import ClassVar, Self

import pytest
from AkonadiCore import Akonadi  # type: ignore

from src.akonadi.client import AkonadiClient
from src.akonadi.dbus.client import AkonadiDBus
from akonadi.utils import AkonadiUtils

log = getLogger(__name__)


class ResourceError(Exception):
    pass


class Resource:
    RESOURCE_TYPE: ClassVar[str]

    def __init__(self, akonadi_client: AkonadiClient, dbus: AkonadiDBus, identifier: str) -> None:
        self._dbus = dbus
        self._identifier = identifier
        self.akonadi_client = akonadi_client

    @classmethod
    async def create(cls, akonadi_client: AkonadiClient, dbus: AkonadiDBus) -> Self:
        log.debug("Creating %s resource via D-Bus", cls.RESOURCE_TYPE)

        createJob = Akonadi.AgentInstanceCreateJob(cls.RESOURCE_TYPE)
        createJob.start()
        AkonadiUtils.wait_for_job(createJob)

        instance_id = createJob.instance().identifier()

        timeout = 0.0 if os.environ.get("AKONADI_DEBUG_WAIT", None) else 10.0
        start = time.time()
        while not createJob.instance().isValid():
            if time.time() - start > timeout:
                raise ResourceError(f"Resource did not become valid in time: {instance_id}")
            await asyncio.sleep(0.5)

        return cls(akonadi_client, dbus, instance_id)

    async def remove(self) -> None:
        log.debug("Removing %s resource via Agent Manager", self.identifier)

        instance = Akonadi.AgentManager.self().instance(self._identifier)
        Akonadi.AgentManager.self().removeInstance(instance)

        # Give time to shut down the resource fully
        await asyncio.sleep(0.5)

    async def synchronize(self) -> None:
        log.debug("Synchronizing %s resource via Agent Manager", self.RESOURCE_TYPE)

        instance = Akonadi.AgentManager.self().instance(self._identifier)

        resourceSynchroJob = Akonadi.ResourceSynchronizationJob(instance)
        resourceSynchroJob.start()
        AkonadiUtils.wait_for_job(resourceSynchroJob)

        await AkonadiUtils.wait_for_status(self._identifier, 0)

        log.debug("%s resource synchronized", self.RESOURCE_TYPE)

    @property
    def identifier(self) -> str:
        return self._identifier

    def resolve_collection(self, collection_name: str) -> Akonadi.Collection:
        path = collection_name.split("/")

        collections = self.akonadi_client.list_collections(parent_id=0, first_level=True)
        resource_root = next(filter(lambda c: c.resource() == self.identifier, collections), None)
        if not resource_root:
            pytest.fail("Resource root collection not found")

        def resolve_recursive(parent: Akonadi.Collection, path: list[str]):
            if not path:
                return parent

            collections = self.akonadi_client.list_collections(
                parent_id=parent.id(), first_level=True
            )
            collection = next(filter(lambda c: c.name() == path[0], collections), None)
            if not collection:
                pytest.fail(f"Collection {collection_name} not found: {path[0]} does not exist!")

            return resolve_recursive(collection, path[1:])

        return resolve_recursive(resource_root, path)

    async def sync_collection(self, collection_name: str) -> None:
        collection = self.resolve_collection(collection_name)
        Akonadi.AgentManager.self().synchronizeCollection(collection, False)

        # to be sure that the collection has been synchronized correctly, we must wait for the instance to be running, then idle again
        # because there isn't a job we can wait, the instance may be idle at first without actually being synced (sync not triggered yet / status not changed yet)
        await AkonadiUtils.wait_for_status(self._identifier, 1)
        await AkonadiUtils.wait_for_status(self._identifier, 0)

    def list_collections(self) -> list[Akonadi.Collection]:
        collections = self.akonadi_client.list_collections(parent_id=0, first_level=True)
        resource_root = next(filter(lambda c: c.resource() == self.identifier, collections), None)
        if not resource_root:
            pytest.fail("Resource root collection not found")

        return self.akonadi_client.list_collections(parent_id=resource_root.id())

    def list_items(self, collection_name_or_id: str | int) -> list[Akonadi.Item]:
        if isinstance(collection_name_or_id, str):
            collection = self.resolve_collection(collection_name_or_id)
            if not collection:
                pytest.fail(f"Collection {collection_name_or_id} not found")

            collection_id = collection.id()
        else:
            collection_id = int(collection_name_or_id)

        return self.akonadi_client.list_items(collection_id=collection_id)

    def delete_collection(self, collection_name: str) -> None:
        collection = self.resolve_collection(collection_name)
        self.akonadi_client.delete_collection(collection.id())

    def add_flag(self, item_id: int, flag: str) -> None:
        item = self.akonadi_client.item_by_id(item_id)
        item.setFlag(flag.encode())

        modifyJob = Akonadi.ItemModifyJob(item)
        AkonadiUtils.wait_for_job(modifyJob)

    async def setOnline(self, online: bool) -> None:
        """
        Pass the ressource to online/offline status, effectively connecting/disconnecting it to any imap/dav server it was configured for
        """
        instance = Akonadi.AgentManager.self().instance(self._identifier)
        instance.setIsOnline(online)
