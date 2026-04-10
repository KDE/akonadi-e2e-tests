# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from typing import override

from AkonadiCore import Akonadi  # type: ignore

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
            f"{self._identifier}_{self.akonadi_client.akonadi_instance_name}rc,$default$"
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

        instance = Akonadi.AgentManager.self().instance(self._identifier)
        instance.reconfigure()

        await AkonadiUtils.wait_for_status(self._identifier, 0)

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
