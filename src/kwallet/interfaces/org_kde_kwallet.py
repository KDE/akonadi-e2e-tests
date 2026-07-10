# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later


# Generated using `sdbus` with some manual edits.
# ```
# python3 -m sdbus gen-from-connection --block org.kde.KWallet /modules/kwalletd6
# ```

from __future__ import annotations

from typing import Any

from sdbus import (
    DbusDeprecatedFlag,
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgKdeKWalletInterface(
    DbusInterfaceCommon,
    interface_name="org.kde.KWallet",
):
    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="isEnabled",
    )
    def is_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="sxs",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="open",
    )
    def open(
        self,
        wallet: str,
        w_id: int,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="sxs",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="openPath",
    )
    def open_path(
        self,
        path: str,
        w_id: int,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="sb",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="close",
    )
    def close(
        self,
        wallet: str,
        force: bool,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="ibs",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="close",
    )
    def close_handle(
        self,
        handle: int,
        force: bool,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="is",
        flags=DbusUnprivilegedFlag,
        method_name="sync",
    )
    def sync(
        self,
        handle: int,
        appid: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="deleteWallet",
    )
    def delete_wallet(
        self,
        wallet: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="isOpen",
    )
    def is_open(
        self,
        wallet: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="i",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="isOpen",
    )
    def is_handle_open(
        self,
        handle: int,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="users",
    )
    def users(
        self,
        wallet: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="sxs",
        flags=DbusUnprivilegedFlag,
        method_name="changePassword",
    )
    def change_password(
        self,
        wallet: str,
        w_id: int,
        appid: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="wallets",
    )
    def wallets(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="is",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="folderList",
    )
    def folder_list(
        self,
        handle: int,
        appid: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="iss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="hasFolder",
    )
    def has_folder(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="iss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="createFolder",
    )
    def create_folder(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="iss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="removeFolder",
    )
    def remove_folder(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="iss",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="entryList",
    )
    def entry_list(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="ay",
        flags=DbusUnprivilegedFlag,
        method_name="readEntry",
    )
    def read_entry(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> bytes:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="ay",
        flags=DbusUnprivilegedFlag,
        method_name="readMap",
    )
    def read_map(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> bytes:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="readPassword",
    )
    def read_password(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="a{sv}",
        flags=DbusDeprecatedFlag | DbusUnprivilegedFlag,
        method_name="readEntryList",
    )
    def read_entry_list(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method(
        input_signature="iss",
        result_signature="a{sv}",
        flags=DbusUnprivilegedFlag,
        method_name="entriesList",
    )
    def entries_list(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="a{sv}",
        flags=DbusDeprecatedFlag | DbusUnprivilegedFlag,
        method_name="readMapList",
    )
    def read_map_list(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method(
        input_signature="iss",
        result_signature="a{sv}",
        flags=DbusUnprivilegedFlag,
        method_name="mapList",
    )
    def map_list(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="a{sv}",
        flags=DbusDeprecatedFlag | DbusUnprivilegedFlag,
        method_name="readPasswordList",
    )
    def read_password_list(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method(
        input_signature="iss",
        result_signature="a{sv}",
        flags=DbusUnprivilegedFlag,
        method_name="passwordList",
    )
    def password_list(
        self,
        handle: int,
        folder: str,
        appid: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method(
        input_signature="issss",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="renameEntry",
    )
    def rename_entry(
        self,
        handle: int,
        folder: str,
        old_name: str,
        new_name: str,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="issayis",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="writeEntry",
    )
    def write_entry_with_type(
        self,
        handle: int,
        folder: str,
        key: str,
        value: bytes,
        entry_type: int,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="issays",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="writeEntry",
    )
    def write_entry(
        self,
        handle: int,
        folder: str,
        key: str,
        value: bytes,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="issays",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="writeMap",
    )
    def write_map(
        self,
        handle: int,
        folder: str,
        key: str,
        value: bytes,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="issss",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="writePassword",
    )
    def write_password(
        self,
        handle: int,
        folder: str,
        key: str,
        value: str,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="hasEntry",
    )
    def has_entry(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="entryType",
    )
    def entry_type(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="isss",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="removeEntry",
    )
    def remove_entry(
        self,
        handle: int,
        folder: str,
        key: str,
        appid: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="ss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="disconnectApplication",
    )
    def disconnect_application(
        self,
        wallet: str,
        application: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="reconfigure",
    )
    def reconfigure(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="ss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="folderDoesNotExist",
    )
    def folder_does_not_exist(
        self,
        wallet: str,
        folder: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="sss",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="keyDoesNotExist",
    )
    def key_does_not_exist(
        self,
        wallet: str,
        folder: str,
        key: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="closeAllWallets",
    )
    def close_all_wallets(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="networkWallet",
    )
    def network_wallet(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="localWallet",
    )
    def local_wallet(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="sayi",
        flags=DbusUnprivilegedFlag,
        method_name="pamOpen",
    )
    def pam_open(
        self,
        wallet: str,
        password_hash: bytes,
        session_timeout: int,
    ) -> None:
        raise NotImplementedError
