# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgFreedesktopAkonadiResourceInterface(
    DbusInterfaceCommon,
    interface_name="org.freedesktop.Akonadi.Resource",
):
    @dbus_method(
        input_signature="axaay",
        flags=DbusUnprivilegedFlag,
        method_name="requestItemDelivery",
    )
    def request_item_delivery(
        self,
        uids: list[int],
        parts: list[bytes],
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="synchronize",
    )
    def synchronize(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="synchronizeCollectionTree",
    )
    def synchronize_collection_tree(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="xb",
        flags=DbusUnprivilegedFlag,
        method_name="synchronizeCollection",
    )
    def synchronize_collection(
        self,
        collection_id: int,
        recursive: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="x",
        flags=DbusUnprivilegedFlag,
        method_name="synchronizeCollectionAttributes",
    )
    def synchronize_collection_attributes(
        self,
        collection_id: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="synchronizeTags",
    )
    def synchronize_tags(
        self,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="setName",
    )
    def set_name(
        self,
        name: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="name",
    )
    def name(
        self,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="setActivities",
    )
    def set_activities(
        self,
        name: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="activities",
    )
    def activities(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="setActivitiesEnabled",
    )
    def set_activities_enabled(
        self,
        en: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="activitiesEnabled",
    )
    def activities_enabled(
        self,
    ) -> bool:
        raise NotImplementedError
