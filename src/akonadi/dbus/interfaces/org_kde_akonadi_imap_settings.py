# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgKdeAkonadiImapSettingsInterface(
    DbusInterfaceCommon,
    interface_name="org.kde.Akonadi.Imap.Settings",
):
    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="save",
    )
    def save(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="imapServer",
    )
    def imap_server(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setImapServer",
    )
    def set_imap_server(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="imapPort",
    )
    def imap_port(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setImapPort",
    )
    def set_imap_port(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="userName",
    )
    def user_name(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setUserName",
    )
    def set_user_name(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="safety",
    )
    def safety(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSafety",
    )
    def set_safety(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="overrideEncryption",
    )
    def override_encryption(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setOverrideEncryption",
    )
    def set_override_encryption(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="authentication",
    )
    def authentication(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setAuthentication",
    )
    def set_authentication(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="subscriptionEnabled",
    )
    def subscription_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setSubscriptionEnabled",
    )
    def set_subscription_enabled(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="sessionTimeout",
    )
    def session_timeout(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setSessionTimeout",
    )
    def set_session_timeout(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="useProxy",
    )
    def use_proxy(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setUseProxy",
    )
    def set_use_proxy(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="disconnectedModeEnabled",
    )
    def disconnected_mode_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setDisconnectedModeEnabled",
    )
    def set_disconnected_mode_enabled(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="intervalCheckEnabled",
    )
    def interval_check_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setIntervalCheckEnabled",
    )
    def set_interval_check_enabled(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="intervalCheckTime",
    )
    def interval_check_time(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setIntervalCheckTime",
    )
    def set_interval_check_time(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="retrieveMetadataOnFolderListing",
    )
    def retrieve_metadata_on_folder_listing(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setRetrieveMetadataOnFolderListing",
    )
    def set_retrieve_metadata_on_folder_listing(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="automaticExpungeEnabled",
    )
    def automatic_expunge_enabled(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setAutomaticExpungeEnabled",
    )
    def set_automatic_expunge_enabled(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="trashCollection",
    )
    def trash_collection(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="setTrashCollection",
    )
    def set_trash_collection(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="trashCollectionMigrated",
    )
    def trash_collection_migrated(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setTrashCollectionMigrated",
    )
    def set_trash_collection_migrated(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="useDefaultIdentity",
    )
    def use_default_identity(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setUseDefaultIdentity",
    )
    def set_use_default_identity(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="accountIdentity",
    )
    def account_identity(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setAccountIdentity",
    )
    def set_account_identity(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="knownMailBoxes",
    )
    def known_mail_boxes(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="setKnownMailBoxes",
    )
    def set_known_mail_boxes(
        self,
        arg_0: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="idleRidPath",
    )
    def idle_rid_path(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="setIdleRidPath",
    )
    def set_idle_rid_path(
        self,
        arg_0: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="sieveSupport",
    )
    def sieve_support(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveSupport",
    )
    def set_sieve_support(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="sieveReuseConfig",
    )
    def sieve_reuse_config(
        self,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveReuseConfig",
    )
    def set_sieve_reuse_config(
        self,
        arg_0: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="sievePort",
    )
    def sieve_port(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setSievePort",
    )
    def set_sieve_port(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="sieveAlternateUrl",
    )
    def sieve_alternate_url(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveAlternateUrl",
    )
    def set_sieve_alternate_url(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="alternateAuthentication",
    )
    def alternate_authentication(
        self,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="setAlternateAuthentication",
    )
    def set_alternate_authentication(
        self,
        arg_0: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="sieveVacationFilename",
    )
    def sieve_vacation_filename(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveVacationFilename",
    )
    def set_sieve_vacation_filename(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="sieveCustomUsername",
    )
    def sieve_custom_username(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveCustomUsername",
    )
    def set_sieve_custom_username(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="sieveCustomAuthentification",
    )
    def sieve_custom_authentification(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setSieveCustomAuthentification",
    )
    def set_sieve_custom_authentification(
        self,
        arg_0: str,
    ) -> None:
        raise NotImplementedError
