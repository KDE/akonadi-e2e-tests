from __future__ import annotations

from sdbus import (
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
)


class OrgKdeAkonadiDavGroupwareSettingsInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.kde.Akonadi.davGroupware.Settings",
):
    @dbus_method_async(
        flags=DbusUnprivilegedFlag,
        method_name="save",
        result_args_names=(),
    )
    async def save(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="settingsVersion",
    )
    async def settings_version(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setSettingsVersion",
        result_args_names=(),
    )
    async def set_settings_version(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="displayName",
    )
    async def display_name(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setDisplayName",
        result_args_names=(),
    )
    async def set_display_name(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="refreshInterval",
    )
    async def refresh_interval(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setRefreshInterval",
        result_args_names=(),
    )
    async def set_refresh_interval(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="remoteUrls",
    )
    async def remote_urls(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="setRemoteUrls",
        result_args_names=(),
    )
    async def set_remote_urls(
        self,
        arg_0: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="defaultUsername",
    )
    async def default_username(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setDefaultUsername",
        result_args_names=(),
    )
    async def set_default_username(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="limitSyncRange",
    )
    async def limit_sync_range(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setLimitSyncRange",
        result_args_names=(),
    )
    async def set_limit_sync_range(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="syncRangeStartNumber",
    )
    async def sync_range_start_number(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSyncRangeStartNumber",
        result_args_names=(),
    )
    async def set_sync_range_start_number(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="syncRangeStartType",
    )
    async def sync_range_start_type(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSyncRangeStartType",
        result_args_names=(),
    )
    async def set_sync_range_start_type(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="collectionsUrlsMappings",
    )
    async def collections_urls_mappings(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setCollectionsUrlsMappings",
        result_args_names=(),
    )
    async def set_collections_urls_mappings(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="readOnly",
    )
    async def read_only(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setReadOnly",
        result_args_names=(),
    )
    async def set_read_only(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="u",
        flags=DbusUnprivilegedFlag,
        method_name="accountId",
    )
    async def account_id(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="u",
        flags=DbusUnprivilegedFlag,
        method_name="setAccountId",
        result_args_names=(),
    )
    async def set_account_id(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="accountServices",
    )
    async def account_services(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="setAccountServices",
        result_args_names=(),
    )
    async def set_account_services(
        self,
        arg_0: list[str],
    ) -> None:
        raise NotImplementedError
