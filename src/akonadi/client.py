# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import asyncio
from logging import getLogger
from tempfile import NamedTemporaryFile

from src.akonadi.env import AkonadiEnv
from src.akonadi.model import Agent, AgentStatus, Collection, Item, ListAgentsResult

log = getLogger(__name__)

__all__ = [
    "AkonadiClient",
    "ClientError",
    "Collection",
    "Item",
    "Agent",
    "AgentStatus",
    "ListAgentsResult",
]


class ClientError(Exception):
    pass


class AkonadiClient:
    def __init__(self, env: AkonadiEnv) -> None:
        self._env = env

    @property
    def akonadi_instance_name(self) -> str:
        return self._env.instance_id

    async def _execute_client(self, args: str) -> bytes:
        log.debug("Executing akonadiclient %s", args)
        client = await asyncio.create_subprocess_shell(
            f"akonadiclient {args}",
            env={
                **self._env.environ,
                # dangerous operations (like deletion) must be allowed explicitly via envvar
                "AKONADICLIENT_DANGEROUS": "enabled",
            },
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await client.communicate()
        if client.returncode != 0:
            raise ClientError(stderr.decode())

        return stdout

    async def collection_by_id(self, collection_id: int) -> Collection | None:
        return Collection.model_validate_json(
            await self._execute_client(f"info -c --json {collection_id}"),
            by_alias=True,
        )

    async def list_collections(
        self, parent_id: int | None = None, first_level: bool = False
    ) -> list[Collection]:
        root = Collection.model_validate_json(
            await self._execute_client(
                f"list -c -l {'-R' if not first_level else ''} --json {parent_id or 0}"
            ),
            by_alias=True,
        )

        def flatten(collections: list[Collection], parent: Collection) -> list[Collection]:
            r = [parent]
            for child in parent.child_collections:
                r.extend(flatten(collections, child))
            return r

        return flatten(root.child_collections, root)

    async def item_by_id(self, item_id: int) -> Item | None:
        return Item.model_validate_json(
            await self._execute_client(f"info -i --json {item_id}"),
            by_alias=True,
        )

    async def list_items(self, collection_id: int) -> list[Item]:
        return Collection.model_validate_json(
            await self._execute_client(f"list -i -l --json {collection_id}"),
            by_alias=True,
        ).child_items

    async def list_agents(self) -> list[Agent]:
        return ListAgentsResult.model_validate_json(
            await self._execute_client("agents --list --json"),
            by_alias=True,
        ).root

    async def agent_by_identifier(self, identifier: str) -> Agent | None:
        agents = ListAgentsResult.model_validate_json(
            await self._execute_client(f"agents --info --json {identifier}"),
            by_alias=True,
        ).root
        return agents[0] if agents else None

    async def add_item(self, collection_id: int, data: bytes, mime_type: str) -> None:
        with NamedTemporaryFile(delete_on_close=False) as f:
            f.write(data)
            f.close()

            # TODO: patch akonadiclient to return the ID of the inserted item
            await self._execute_client(f"add -m {mime_type} {collection_id} {f.name}")

    async def delete_item(self, item_id: int) -> None:
        await self._execute_client(f"delete -i {item_id}")
