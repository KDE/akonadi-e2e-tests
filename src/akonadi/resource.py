# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import time
from abc import ABC, abstractmethod
from logging import getLogger
from typing import ClassVar, Self

import pytest
from AkonadiCore import Akonadi  # type: ignore

from src.akonadi.client import AkonadiClient
from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.utils import AkonadiUtils

log = getLogger(__name__)


class ResourceError(Exception):
    pass


class Resource(ABC):
    RESOURCE_TYPE: ClassVar[str]

    def __init__(
        self, akonadi_client: AkonadiClient, dbus: AkonadiDBus, instance: Akonadi.AgentInstance
    ) -> None:
        self._dbus = dbus
        self._identifier = instance.identifier()
        self.akonadi_client = akonadi_client

    @classmethod
    def create(cls, akonadi_client: AkonadiClient, dbus: AkonadiDBus) -> Self:
        log.debug("Creating %s resource via D-Bus", cls.RESOURCE_TYPE)

        createJob = Akonadi.AgentInstanceCreateJob(cls.RESOURCE_TYPE)
        createJob.start()
        AkonadiUtils.wait_for_job(createJob)

        instance = createJob.instance()

        assert instance.isValid()

        return cls(akonadi_client, dbus, instance)

    @property
    def instance(self) -> Akonadi.AgentInstance:
        return Akonadi.AgentManager.self().instance(self._identifier)

    async def remove(self) -> None:
        log.debug("Removing %s resource via Agent Manager", self.identifier)

        Akonadi.AgentManager.self().removeInstance(self.instance)

        # Give time to shut down the resource fully
        time.sleep(0.5)

    def synchronize(self) -> None:
        log.debug("Synchronizing %s resource via Agent Manager", self.RESOURCE_TYPE)

        resourceSynchroJob = Akonadi.ResourceSynchronizationJob(self.instance)
        resourceSynchroJob.start()
        AkonadiUtils.wait_for_job(resourceSynchroJob)

        AkonadiUtils.wait_for_status(self._identifier, 0)

        log.debug("%s resource synchronized", self.RESOURCE_TYPE)

    @property
    def identifier(self) -> str:
        return self._identifier

    def get_root_collection(self) -> Akonadi.Collection:
        collections = self.akonadi_client.list_collections(parent_id=0, first_level=True)
        resource_root = next(filter(lambda c: c.resource() == self.identifier, collections), None)
        if not resource_root:
            pytest.fail("Resource root collection not found")
        return resource_root

    @abstractmethod
    def resolve_collection(self, collection_name: str) -> Akonadi.Collection:
        raise NotImplementedError

    def sync_collection(self, collection_name: str) -> None:
        collection = self.resolve_collection(collection_name)
        Akonadi.AgentManager.self().synchronizeCollection(collection, False)

        # to be sure that the collection has been synchronized correctly, we must wait for the instance to be running, then idle again
        # because there isn't a job we can wait, the instance may be idle at first without actually being synced (sync not triggered yet / status not changed yet)
        AkonadiUtils.wait_for_status(self._identifier, 1)
        AkonadiUtils.wait_for_status(self._identifier, 0)

    def list_collections(self) -> list[Akonadi.Collection]:
        return self.akonadi_client.list_collections(parent_id=self.get_root_collection().id())

    def list_items(
        self, collection_name_or_id: str | int, full_payload: bool = True
    ) -> list[Akonadi.Item]:
        if isinstance(collection_name_or_id, str):
            collection = self.resolve_collection(collection_name_or_id)
            if not collection:
                pytest.fail(f"Collection {collection_name_or_id} not found")

            collection_id = collection.id()
        else:
            collection_id = int(collection_name_or_id)

        return self.akonadi_client.list_items(
            collection_id=collection_id, full_payload=full_payload
        )

    def delete_collection(self, collection_name: str) -> None:
        collection = self.resolve_collection(collection_name)
        self.akonadi_client.delete_collection(collection.id())

    def rename_collection(self, collection_name: str, new_name: str) -> None:
        collection = self.resolve_collection(collection_name)
        self.akonadi_client.rename_collection(collection.id(), new_name)

    def add_flag(self, item_id: int, flag: str) -> None:
        item = self.akonadi_client.item_by_id(item_id)
        item.setFlag(flag.encode())

        modifyJob = Akonadi.ItemModifyJob(item)
        AkonadiUtils.wait_for_job(modifyJob)

    def clear_flag(self, item_id: int, flag: str) -> None:
        item = self.akonadi_client.item_by_id(item_id)
        item.clearFlag(flag.encode())

        modifyJob = Akonadi.ItemModifyJob(item)
        AkonadiUtils.wait_for_job(modifyJob)

    def set_online(self, online: bool) -> None:
        """
        Pass the ressource to online/offline status, effectively connecting/disconnecting it to any imap/dav server it was configured for
        """
        time.sleep(0.2)
        self.instance.setIsOnline(online)
        AkonadiUtils.wait_for_online(self._identifier, online)
        if online:
            self.wait_resource_is_idle()

    def wait_resource_is_idle(self, timeout_ms: int = 30000):
        assert self.instance.isOnline(), "Resource must be online to wait for idle"
        start_time = time.monotonic()
        timeout_s = timeout_ms / 1000.0

        while self.instance.taskList():
            log.info("Waiting for resource %s to be idle", self.identifier)
            elapsed = time.monotonic() - start_time
            if elapsed > timeout_s:
                pytest.fail(
                    f"Timed out after {timeout_s} seconds waiting for resource {self.identifier} to be idle"
                )
            time.sleep(0.05)
