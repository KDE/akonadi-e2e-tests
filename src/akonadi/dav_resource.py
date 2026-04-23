# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
# SPDX-FileCopyrightText: 2026 Benjamin Port <benjamin.port@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from typing import override
from urllib.parse import unquote

import pytest
from AkonadiCore import Akonadi  # type: ignore
from PySide6.QtGui import QColor  # type: ignore

from src.akonadi.client import AkonadiClient
from src.akonadi.dbus.client import AkonadiDBus
from src.akonadi.dbus.interfaces.org_kde_akonadi_davgroupware_settings import (
    OrgKdeAkonadiDavGroupwareSettingsInterface,
)
from src.akonadi.resource import Resource
from src.akonadi.utils import AkonadiUtils
from src.kwallet.client import KWalletClient

log = getLogger(__name__)


class DAVResource(Resource):
    RESOURCE_TYPE = "akonadi_davgroupware_resource"

    def __init__(self, akonadi_client: AkonadiClient, dbus: AkonadiDBus, identifier: str) -> None:
        super().__init__(akonadi_client, dbus, identifier)
        self._kwallet_key = (
            f"{self._identifier}_{self.akonadi_client.akonadi_instance_name},$default$"
        )

    async def configure(self, base_url: str, username: str, password: str) -> None:
        settings = OrgKdeAkonadiDavGroupwareSettingsInterface.new_proxy(
            self._dbus.resource_service_name(self._identifier),
            "/Settings",
            self._dbus.client,
        )

        # The DAV resource doesn't expose means to set password externally, so we instead
        # store it into KWallet ourselves under the name that the resource expects.
        async with KWalletClient() as kwallet:
            await kwallet.store_password(self._kwallet_key, password)

        await settings.set_settings_version(3)
        await settings.set_remote_urls([f"$default$|CalDav|{base_url}"])
        await settings.set_default_username(username)
        await settings.set_display_name(
            f"akonadi-e2e-test - {self.akonadi_client.akonadi_instance_name}"
        )

        await settings.save()

        self.instance.reconfigure()

        AkonadiUtils.wait_for_status(self._identifier, 0)

    @override
    async def remove(self) -> None:
        await super().remove()

        async with KWalletClient() as kwallet:
            password_exists = await kwallet.get_password(self._kwallet_key) is not None
            if password_exists:
                # Remove the KWallet entry
                await kwallet.remove_password(
                    self._kwallet_key,
                )

            # FIXME: Enable this once the DAV resource is fixed to clean up after itself
            # assert not password_exists

    @override
    def resolve_collection(self, collection_remote_id: str) -> Akonadi.Collection:
        resource_root = self.get_root_collection()

        collections = self.akonadi_client.list_collections(
            parent_id=resource_root.id(), first_level=True
        )
        collection = next(
            (c for c in collections if unquote(c.remoteId()) == unquote(collection_remote_id)), None
        )
        if not collection:
            pytest.fail(f"Collection {collection_remote_id} not found")

        return collection

    def collection_from_display_name(self, name: str) -> Akonadi.Collection:
        resource_root = self.get_root_collection()

        collections = self.akonadi_client.list_collections(
            parent_id=resource_root.id(), first_level=True
        )
        collection = next((c for c in collections if c.displayName() == name), None)
        if not collection:
            pytest.fail(f"Collection {name} not found")

        return collection

    def get_collection_color(self, collection_name: str) -> str | None:
        collection = self.resolve_collection(collection_name)
        attribute = collection.attribute(b"collectioncolor")
        return bytes(attribute.serialized()).decode() if attribute else None

    def set_collection_color(self, collection_name: str, hex_color: str) -> None:
        collection = self.resolve_collection(collection_name)
        attr = Akonadi.CollectionColorAttribute()
        attr.setColor(QColor.fromString(hex_color))

        new = Akonadi.Collection()
        new.setId(collection.id())
        new.addAttribute(attr.clone())  # clone to give an unmanaged object
        job = Akonadi.CollectionModifyJob(new)

        AkonadiUtils.wait_for_job(job)
