# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from typing import Any

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgFreedesktopAkonadiAgentManagerInterface(
    DbusInterfaceCommon,
    interface_name="org.freedesktop.Akonadi.AgentManager",
):
    @dbus_method(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentTypes",
    )
    def agent_types(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentName",
    )
    def agent_name(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentComment",
    )
    def agent_comment(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentIcon",
    )
    def agent_icon(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentMimeTypes",
    )
    def agent_mime_types(
        self,
        identifier: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentCapabilities",
    )
    def agent_capabilities(
        self,
        identifier: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="a{sv}",
        flags=DbusUnprivilegedFlag,
        method_name="agentCustomProperties",
    )
    def agent_custom_properties(
        self,
        identifier: str,
    ) -> dict[str, tuple[str, Any]]:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="createAgentInstance",
    )
    def create_agent_instance(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="removeAgentInstance",
    )
    def remove_agent_instance(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceType",
    )
    def agent_instance_type(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstances",
    )
    def agent_instances(
        self,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="i",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceStatus",
    )
    def agent_instance_status(
        self,
        identifier: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceStatusMessage",
    )
    def agent_instance_status_message(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="u",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceProgress",
    )
    def agent_instance_progress(
        self,
        identifier: str,
    ) -> int:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceProgressMessage",
    )
    def agent_instance_progress_message(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="ss",
        flags=DbusUnprivilegedFlag,
        method_name="setAgentInstanceName",
    )
    def set_agent_instance_name(
        self,
        identifier: str,
        name: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceName",
    )
    def agent_instance_name(
        self,
        identifier: str,
    ) -> str:
        raise NotImplementedError

    @dbus_method(
        input_signature="sx",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceConfigure",
    )
    def agent_instance_configure(
        self,
        identifier: str,
        window_id: int,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceSynchronize",
    )
    def agent_instance_synchronize(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceSynchronizeCollectionTree",
    )
    def agent_instance_synchronize_collection_tree(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="sxb",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceSynchronizeCollection",
    )
    def agent_instance_synchronize_collection(
        self,
        identifier: str,
        collection: int,
        recursive: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceSynchronizeTags",
    )
    def agent_instance_synchronize_tags(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceOnline",
    )
    def agent_instance_online(
        self,
        identifier: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        input_signature="sb",
        flags=DbusUnprivilegedFlag,
        method_name="setAgentInstanceOnline",
    )
    def set_agent_instance_online(
        self,
        identifier: str,
        state: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="as",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceActivities",
    )
    def agent_instance_activities(
        self,
        identifier: str,
    ) -> list[str]:
        raise NotImplementedError

    @dbus_method(
        input_signature="sas",
        flags=DbusUnprivilegedFlag,
        method_name="setAgentInstanceActivities",
    )
    def set_agent_instance_activities(
        self,
        identifier: str,
        activities: list[str],
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        flags=DbusUnprivilegedFlag,
        method_name="restartAgentInstance",
    )
    def restart_agent_instance(
        self,
        identifier: str,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="sb",
        flags=DbusUnprivilegedFlag,
        method_name="setAgentInstanceActivitiesEnabled",
    )
    def set_agent_instance_activities_enabled(
        self,
        identifier: str,
        en: bool,
    ) -> None:
        raise NotImplementedError

    @dbus_method(
        input_signature="s",
        result_signature="b",
        flags=DbusUnprivilegedFlag,
        method_name="agentInstanceActivitiesEnabled",
    )
    def agent_instance_activities_enabled(
        self,
        identifier: str,
    ) -> bool:
        raise NotImplementedError
