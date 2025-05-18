# SPDX-FileContributor: Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommonAsync,
    DbusUnprivilegedFlag,
    dbus_method_async,
)


class OrgKdeAkonadiImapSettingsInterface(
    DbusInterfaceCommonAsync,
    interface_name="org.kde.Akonadi.Imap.Settings",
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
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="imapServer",
    )
    async def imap_server(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setImapServer",
        result_args_names=(),
    )
    async def set_imap_server(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="imapPort",
    )
    async def imap_port(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setImapPort",
        result_args_names=(),
    )
    async def set_imap_port(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="userName",
    )
    async def user_name(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setUserName",
        result_args_names=(),
    )
    async def set_user_name(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="safety",
    )
    async def safety(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSafety",
        result_args_names=(),
    )
    async def set_safety(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="overrideEncryption",
    )
    async def override_encryption(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setOverrideEncryption",
        result_args_names=(),
    )
    async def set_override_encryption(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="authentication",
    )
    async def authentication(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setAuthentication",
        result_args_names=(),
    )
    async def set_authentication(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="subscriptionEnabled",
    )
    async def subscription_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setSubscriptionEnabled",
        result_args_names=(),
    )
    async def set_subscription_enabled(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="sessionTimeout",
    )
    async def session_timeout(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setSessionTimeout",
        result_args_names=(),
    )
    async def set_session_timeout(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="useProxy",
    )
    async def use_proxy(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setUseProxy",
        result_args_names=(),
    )
    async def set_use_proxy(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="disconnectedModeEnabled",
    )
    async def disconnected_mode_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setDisconnectedModeEnabled",
        result_args_names=(),
    )
    async def set_disconnected_mode_enabled(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="intervalCheckEnabled",
    )
    async def interval_check_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setIntervalCheckEnabled",
        result_args_names=(),
    )
    async def set_interval_check_enabled(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="intervalCheckTime",
    )
    async def interval_check_time(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setIntervalCheckTime",
        result_args_names=(),
    )
    async def set_interval_check_time(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="retrieveMetadataOnFolderListing",
    )
    async def retrieve_metadata_on_folder_listing(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setRetrieveMetadataOnFolderListing",
        result_args_names=(),
    )
    async def set_retrieve_metadata_on_folder_listing(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="automaticExpungeEnabled",
    )
    async def automatic_expunge_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setAutomaticExpungeEnabled",
        result_args_names=(),
    )
    async def set_automatic_expunge_enabled(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="trashCollection",
    )
    async def trash_collection(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="setTrashCollection",
        result_args_names=(),
    )
    async def set_trash_collection(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="trashCollectionMigrated",
    )
    async def trash_collection_migrated(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setTrashCollectionMigrated",
        result_args_names=(),
    )
    async def set_trash_collection_migrated(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="useDefaultIdentity",
    )
    async def use_default_identity(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setUseDefaultIdentity",
        result_args_names=(),
    )
    async def set_use_default_identity(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="accountIdentity",
    )
    async def account_identity(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setAccountIdentity",
        result_args_names=(),
    )
    async def set_account_identity(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="knownMailBoxes",
    )
    async def known_mail_boxes(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="setKnownMailBoxes",
        result_args_names=(),
    )
    async def set_known_mail_boxes(
        self,
        arg_0: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="idleRidPath",
    )
    async def idle_rid_path(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="setIdleRidPath",
        result_args_names=(),
    )
    async def set_idle_rid_path(
        self,
        arg_0: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="sieveSupport",
    )
    async def sieve_support(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveSupport",
        result_args_names=(),
    )
    async def set_sieve_support(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="sieveReuseConfig",
    )
    async def sieve_reuse_config(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveReuseConfig",
        result_args_names=(),
    )
    async def set_sieve_reuse_config(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="sievePort",
    )
    async def sieve_port(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setSievePort",
        result_args_names=(),
    )
    async def set_sieve_port(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="sieveAlternateUrl",
    )
    async def sieve_alternate_url(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveAlternateUrl",
        result_args_names=(),
    )
    async def set_sieve_alternate_url(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="alternateAuthentication",
    )
    async def alternate_authentication(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setAlternateAuthentication",
        result_args_names=(),
    )
    async def set_alternate_authentication(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="sieveVacationFilename",
    )
    async def sieve_vacation_filename(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveVacationFilename",
        result_args_names=(),
    )
    async def set_sieve_vacation_filename(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="sieveCustomUsername",
    )
    async def sieve_custom_username(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveCustomUsername",
        result_args_names=(),
    )
    async def set_sieve_custom_username(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method_async(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="sieveCustomAuthentification",
    )
    async def sieve_custom_authentification(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method_async(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveCustomAuthentification",
        result_args_names=(),
    )
    async def set_sieve_custom_authentification(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError
