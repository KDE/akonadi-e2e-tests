# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from AkonadiCore import Akonadi  # type: ignore

from src.akonadi.env import AkonadiEnv
from akonadi.utils import AkonadiUtils

log = getLogger(__name__)

__all__ = [
    "AkonadiClient",
    "ClientError",
]


class ClientError(Exception):
    pass


class AkonadiClient:
    def __init__(self, env: AkonadiEnv) -> None:
        self._env = env

    @property
    def akonadi_instance_name(self) -> str:
        return self._env.instance_id

    def collection_by_id(self, collection_id: int) -> Akonadi.Collection | None:
        if collection_id <= 0:
            return Akonadi.Collection.root()

        else:
            job = Akonadi.CollectionFetchJob([collection_id])
            AkonadiUtils.wait_for_job(job)

            if len(job.collections()) != 1:
                raise ClientError(f"Found {len(job.collections())} collections when expecting 1")

            return job.collections()[0]

    def list_collections(
        self, parent_id: int | None = None, first_level: bool = False
    ) -> list[Akonadi.Collection]:
        fetched_collections = [self.collection_by_id(parent_id or 0)]

        collection = Akonadi.Collection()
        collection.setId(parent_id or 0)
        type = (
            Akonadi.CollectionFetchJob.FirstLevel
            if first_level
            else Akonadi.CollectionFetchJob.Recursive
        )
        job = Akonadi.CollectionFetchJob(collection, type)
        AkonadiUtils.wait_for_job(job)

        fetched_collections.extend(job.collections())

        return fetched_collections

    def delete_collection(self, collection_id: int) -> None:
        collection = Akonadi.Collection()
        collection.setId(collection_id)

        job = Akonadi.CollectionDeleteJob(collection)

        AkonadiUtils.wait_for_job(job)

    def item_by_id(self, item_id: int) -> Akonadi.Item:
        item = Akonadi.Item()
        item.setId(item_id)

        job = Akonadi.ItemFetchJob(item)
        AkonadiUtils.wait_for_job(job)

        if len(job.items()) != 1:
            raise ClientError(f"Found {len(job.items())} items when expecting 1")
        return job.items()[0]

    def list_items(self, collection_id: int) -> list[Akonadi.Item]:
        collection = Akonadi.Collection()
        collection.setId(collection_id)

        job = Akonadi.ItemFetchJob(collection)
        AkonadiUtils.wait_for_job(job)

        return job.items()

    def list_agents(self) -> list[Akonadi.AgentInstance]:
        return Akonadi.AgentManager.self().instances()

    def agent_by_identifier(self, identifier: str) -> Akonadi.AgentInstance | None:
        agent = Akonadi.AgentManager.self().instance(identifier)
        return agent if agent.isValid() else None

    def add_item(self, collection_id: int, data: bytes, mime_type: str) -> None:
        item = Akonadi.Item()
        item.setMimeType(mime_type)
        item.setPayloadFromData(data)

        collection = Akonadi.Collection()
        collection.setId(collection_id)

        job = Akonadi.ItemCreateJob(item, collection)
        AkonadiUtils.wait_for_job(job)

    def delete_item(self, item_id: int) -> None:
        item = Akonadi.Item()
        item.setId(item_id)

        job = Akonadi.ItemDeleteJob(item)
        AkonadiUtils.wait_for_job(job)

    def move_item(self, item_id: int, destination_id: int) -> None:
        item = Akonadi.Item()
        item.setId(item_id)

        destination = Akonadi.Collection()
        destination.setId(destination_id)

        job = Akonadi.ItemMoveJob(item, destination)

        AkonadiUtils.wait_for_job(job)

    def copy_item(self, item_id: int, destination_id: int) -> None:
        item = Akonadi.Item()
        item.setId(item_id)

        destination = Akonadi.Collection()
        destination.setId(destination_id)

        job = Akonadi.ItemCopyJob(item, destination)

        AkonadiUtils.wait_for_job(job)
