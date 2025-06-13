# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from types import TracebackType

from sdbus import sd_bus_open

from src.kwallet.interfaces.org_kde_kwallet import OrgKdeKWalletInterface

log = getLogger(__name__)


class KWalletClient:
    KWALLET_SERVICE_NAME = "org.kde.kwalletd6"
    KWALLET_SERVICE_OBJECT_PATH = "/modules/kwalletd6"
    SERVICE_NAME = "Passwords"

    def __init__(self) -> None:
        self._bus = sd_bus_open()
        self._wallet = OrgKdeKWalletInterface.new_proxy(
            self.KWALLET_SERVICE_NAME,
            self.KWALLET_SERVICE_OBJECT_PATH,
            self._bus,
        )
        self._handle: int | None = None

    async def open(self) -> None:
        wallet_name = await self._wallet.network_wallet()
        log.debug("Opening KWallet %s", wallet_name)
        self._handle = await self._wallet.open(wallet_name, 0, self.SERVICE_NAME)

    async def close(self) -> None:
        if self._handle is None:
            return
        log.debug("Closing KWallet %s", self._handle)
        await self._wallet.close_handle(self._handle, force=False, appid=self.SERVICE_NAME)
        self._handle = None

    async def store_password(self, name: str, password: str) -> None:
        if self._handle is None:
            raise RuntimeError("Wallet not open")

        log.debug("Storing password '%s' in KWallet", name)
        await self._wallet.write_password(
            self._handle, self.SERVICE_NAME, name, password, self.SERVICE_NAME
        )

    async def get_password(self, name: str) -> str | None:
        if self._handle is None:
            raise RuntimeError("Wallet not open")

        log.debug("Getting password '%s' from KWallet", name)
        try:
            return await self._wallet.read_password(
                self._handle, self.SERVICE_NAME, name, self.SERVICE_NAME
            )
        except Exception as e:
            log.warning("Password '%s' not found in KWallet: %s", name, e)
            return None

    async def remove_password(self, name: str) -> None:
        if self._handle is None:
            raise RuntimeError("Wallet not open")

        log.debug("Removing password '%s' from KWallet", name)
        result = await self._wallet.remove_entry(
            self._handle, self.SERVICE_NAME, name, self.SERVICE_NAME
        )
        log.debug("Remove entry result: %s", result)

    async def __aenter__(self) -> "KWalletClient":
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()
