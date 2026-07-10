# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger
from types import TracebackType

from src.kwallet.interfaces.org_kde_kwallet import OrgKdeKWalletInterface

log = getLogger(__name__)


class KWalletClient:
    KWALLET_SERVICE_NAME = "org.kde.kwalletd6"
    KWALLET_SERVICE_OBJECT_PATH = "/modules/kwalletd6"
    SERVICE_NAME = "Passwords"

    def __init__(self, service_name: str = "Passwords") -> None:
        self.SERVICE_NAME = service_name
        self._wallet = OrgKdeKWalletInterface(
            self.KWALLET_SERVICE_NAME,
            self.KWALLET_SERVICE_OBJECT_PATH,
        )
        self._handle: int | None = None

    def open(self) -> None:
        wallet_name = self._wallet.network_wallet()
        log.debug("Opening KWallet %s", wallet_name)
        self._handle = self._wallet.open(wallet_name, 0, self.SERVICE_NAME)

    def close(self) -> None:
        if self._handle is None:
            return
        log.debug("Closing KWallet %s", self._handle)
        self._wallet.close_handle(self._handle, force=False, appid=self.SERVICE_NAME)
        self._handle = None

    def store_password(self, name: str, password: str) -> None:
        if self._handle is None:
            raise RuntimeError("Wallet not open")

        log.debug("Storing password '%s' in KWallet", name)
        self._wallet.write_password(
            self._handle, self.SERVICE_NAME, name, password, self.SERVICE_NAME
        )

    def get_password(self, name: str) -> str | None:
        if self._handle is None:
            raise RuntimeError("Wallet not open")

        log.debug("Getting password '%s' from KWallet", name)
        try:
            return self._wallet.read_password(
                self._handle, self.SERVICE_NAME, name, self.SERVICE_NAME
            )
        except Exception as e:
            log.warning("Password '%s' not found in KWallet: %s", name, e)
            return None

    def remove_password(self, name: str) -> None:
        if self._handle is None:
            raise RuntimeError("Wallet not open")

        log.debug("Removing password '%s' from KWallet", name)
        result = self._wallet.remove_entry(self._handle, self.SERVICE_NAME, name, self.SERVICE_NAME)
        log.debug("Remove entry result: %s", result)

    def __enter__(self) -> "KWalletClient":
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
