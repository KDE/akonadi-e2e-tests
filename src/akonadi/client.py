import asyncio
from logging import getLogger
from .env import AkonadiEnv
from .model import Collection, Item

log = getLogger(__name__)


class ClientError(Exception):
    pass


class AkonadiClient:
    def __init__(self, env: AkonadiEnv) -> None:
        self._env = env

    async def _execute_client(self, args: str) -> bytes:
        client = await asyncio.create_subprocess_shell(
            f"akonadiclient {args}",
            env=self._env.environ,
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

    async def list_collections(self, parent_id: int | None = None) -> list[Collection]:
        root = Collection.model_validate_json(
            await self._execute_client(f"list -c -l -R --json {parent_id or 0}"),
            by_alias=True,
        )

        def flatten(
            collections: list[Collection], parent: Collection
        ) -> list[Collection]:
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
