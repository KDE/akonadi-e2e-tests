# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from typing_extensions import override

from src.akonadi.dbus.interfaces.org_kde_akonadi_davgroupware_settings import (
    OrgKdeAkonadiDavGroupwareSettingsInterface,
)
from src.akonadi.resource import Resource
from src.kwallet.client import KWalletClient

log = getLogger(__name__)


class DAVResource(Resource):
    RESOURCE_TYPE = "akonadi_davgroupware_resource"

    @override
    async def configure(
        self, host: str, port: int, username: str, password: str
    ) -> None:
        settings = OrgKdeAkonadiDavGroupwareSettingsInterface.new_proxy(
            self._dbus.resource_service_name(self._instance_id),
            "/Settings",
            self._dbus.client,
        )

        # The DAV resource doesn't expose means to set password externally, so we instead
        # store it into KWallet ourselves under the name that the resource expects.
        async with KWalletClient() as kwallet:
            await kwallet.store_password(
                f"{self._instance_id}_{self._akonadi_client.akonadi_instance_name},$default$",
                "testtest"
            )

        await settings.set_settings_version(3)
        # FIXME: This is nextcloud specific - make it more generic over different DAV servers
        await settings.set_remote_urls(
            [f"$default$|CalDav|http://{host}:{port}/remote.php/dav/"]
        )
        await settings.set_default_username(username)
        await settings.set_display_name(f"akonadi-e2e-test {host}:{port}")

        await settings.save()

        await self._dbus.agent_interface(self._instance_id).reconfigure()

