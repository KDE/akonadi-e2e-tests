from __future__ import annotations

from typing import Any

from sdbus import (
    DbusDeprecatedFlag,
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
    dbus_signal_async,
)


class OrgKdeKWalletInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.kde.KWallet",
):
    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="isEnabled",
    )
    async def is_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sxs",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="open",
    )
    async def open(
        self,
        wallet: str,
        w_id: int,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sxs",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="openPath",
    )
    async def open_path(
        self,
        path: str,
        w_id: int,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sxsb",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="openAsync",
    )
    async def open_async(
        self,
        wallet: str,
        w_id: int,
        appid: str,
        handle_session: bool,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sxsb",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="openPathAsync",
    )
    async def open_path_async(
        self,
        path: str,
        w_id: int,
        appid: str,
        handle_session: bool,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sb",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="close",
    )
    async def close(
        self,
        wallet: str,
        force: bool,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="ibs",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="close",
    )
    async def close_handle(
        self,
        handle: int,
        force: bool,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="is",
        flags=DbusUnprivilegedFlag,
        method_name="sync",
        result_args_names=(),
    )
    async def sync(
        self,
        handle: int,
        appid: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="deleteWallet",
    )
    async def delete_wallet(
        self,
        wallet: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="isOpen",
    )
    async def is_open(
        self,
        wallet: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="isOpen",
    )
    async def is_handle_open(
        self,
        handle: int,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="users",
    )
    async def users(
        self,
        wallet: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sxs",
        flags=DbusUnprivilegedFlag,
        method_name="changePassword",
        result_args_names=(),
    )
    async def change_password(
        self,
        wallet: str,
        w_id: int,
        appid: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="wallets",
    )
    async def wallets(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="is",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="folderList",
    )
    async def folder_list(
        self,
        handle: int,
        appid: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="iss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="hasFolder",
    )
    async def has_folder(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="iss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="createFolder",
    )
    async def create_folder(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="iss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="removeFolder",
    )
    async def remove_folder(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="iss",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="entryList",
    )
    async def entry_list(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="ay",
        flags=DbusUnprivilegedFlag,
        method_name="readEntry",
    )
    async def read_entry(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> bytes:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="ay",
        flags=DbusUnprivilegedFlag,
        method_name="readMap",
    )
    async def read_map(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> bytes:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="readPassword",
    )
    async def read_password(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="a{sv}",
        flags=DbusDeprecatedFlag | DbusUnprivilegedFlag,
        method_name="readEntryList",
    )
    async def read_entry_list(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="iss",
        result_signature="a{sv}",
        flags=DbusUnprivilegedFlag,
        method_name="entriesList",
    )
    async def entries_list(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="a{sv}",
        flags=DbusDeprecatedFlag | DbusUnprivilegedFlag,
        method_name="readMapList",
    )
    async def read_map_list(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="iss",
        result_signature="a{sv}",
        flags=DbusUnprivilegedFlag,
        method_name="mapList",
    )
    async def map_list(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="a{sv}",
        flags=DbusDeprecatedFlag | DbusUnprivilegedFlag,
        method_name="readPasswordList",
    )
    async def read_password_list(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="iss",
        result_signature="a{sv}",
        flags=DbusUnprivilegedFlag,
        method_name="passwordList",
    )
    async def password_list(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="issss",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="renameEntry",
    )
    async def rename_entry(
        self,
        handle: int,
        folder: str,
        old_name: str,
        new_name: str,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="issayis",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="writeEntry",
    )
    async def write_entry_with_type(
        self,
        handle: int,
        folder: str,
        key: str,
        value: bytes,
        entry_type: int,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="issays",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="writeEntry",
    )
    async def write_entry(
        self,
        handle: int,
        folder: str,
        key: str,
        value: bytes,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="issays",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="writeMap",
    )
    async def write_map(
        self,
        handle: int,
        folder: str,
        key: str,
        value: bytes,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="issss",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="writePassword",
    )
    async def write_password(
        self,
        handle: int,
        folder: str,
        key: str,
        value: str,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="hasEntry",
    )
    async def has_entry(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="entryType",
    )
    async def entry_type(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="isss",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="removeEntry",
    )
    async def remove_entry(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="ss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="disconnectApplication",
    )
    async def disconnect_application(
        self,
        wallet: str,
        application: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="reconfigure",
        result_args_names=(),
    )
    async def reconfigure(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="ss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="folderDoesNotExist",
    )
    async def folder_does_not_exist(
        self,
        wallet: str,
        folder: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="keyDoesNotExist",
    )
    async def key_does_not_exist(
        self,
        wallet: str,
        folder: str,
        key: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="closeAllWallets",
        result_args_names=(),
    )
    async def close_all_wallets(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="networkWallet",
    )
    async def network_wallet(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="localWallet",
    )
    async def local_wallet(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="sayi",
        flags=DbusUnprivilegedFlag,
        method_name="pamOpen",
        result_args_names=(),
    )
    async def pam_open(
        self,
        wallet: str,
        password_hash: bytes,
        session_timeout: int,
    ) -> None:
        raise NotImplementedError

    @dbus_signal_async(
        signal_args_names=(),
        signal_name="walletListDirty",
    )
    def wallet_list_dirty(self) -> None:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=('wallet',),
        signal_name="walletCreated",
    )
    def wallet_created(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=('wallet',),
        signal_name="walletOpened",
    )
    def wallet_opened(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="ii",
        signal_args_names=('tId', 'handle'),
        signal_name="walletAsyncOpened",
    )
    def wallet_async_opened(self) -> tuple[int, int]:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=('wallet',),
        signal_name="walletDeleted",
    )
    def wallet_deleted(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=('wallet',),
        signal_name="walletClosed",
    )
    def wallet_closed(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="i",
        signal_args_names=('handle',),
        flags=DbusDeprecatedFlag,
        signal_name="walletClosedId",
    )
    def wallet_handle_closed(self) -> int:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="i",
        signal_args_names=('handle',),
        signal_name="walletClosedId",
    )
    def wallet_closed_id(self) -> int:
        raise NotImplementedError

    @dbus_signal_async(
        signal_args_names=(),
        signal_name="allWalletsClosed",
    )
    def all_wallets_closed(self) -> None:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="s",
        signal_args_names=('wallet',),
        signal_name="folderListUpdated",
    )
    def folder_list_updated(self) -> str:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="ss",
        signal_name="folderUpdated",
    )
    def folder_updated(self) -> tuple[str, str]:
        raise NotImplementedError

    @dbus_signal_async(
        signal_signature="ss",
        signal_args_names=('wallet', 'application'),
        signal_name="applicationDisconnected",
    )
    def application_disconnected(self) -> tuple[str, str]:
        raise NotImplementedError

