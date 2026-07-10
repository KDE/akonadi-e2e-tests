# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)

from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_agent_control import (
    OrgFreedesktopAkonadiAgentControlInterface,
)
from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_agent_manager import (
    OrgFreedesktopAkonadiAgentManagerInterface,
)
from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_controlmanager import (
    OrgFreedesktopAkonadiControlManagerInterface,
)
from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_resource import (
    OrgFreedesktopAkonadiResourceInterface,
)
from src.akonadi.dbus.interfaces.org_freedesktop_akonadi_server import (
    OrgFreedesktopAkonadiServerInterface,
)
from src.test import wait_until

log = getLogger(__name__)


class FreedesktopDbus(
    DbusInterfaceCommon,
    interface_name="org.freedesktop.DBus",
):
    @dbus_method(
        flags=DbusUnprivilegedFlag,
        input_signature="s",
        method_name="NameHasOwner",
        result_signature="b",
    )
    def name_has_owner(
        self,
        service_name: str,
    ) -> bool:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        input_signature="s",
        method_name="GetNameOwner",
        result_signature="s",
    )
    def get_name_owner(self, service_name: str) -> str:
        raise NotImplementedError


class AkonadiDBus:
    """A high-level client for the Akonadi DBus service."""

    def __init__(self, instance_id: str) -> None:
        self._instance_id = instance_id

    @property
    def akonadi_server_service_name(self) -> str:
        return f"org.freedesktop.Akonadi.{self._instance_id}"

    @property
    def akonadi_control_service_name(self) -> str:
        return f"org.freedesktop.Akonadi.Control.{self._instance_id}"

    def resource_service_name(self, instance_id: str) -> str:
        return f"org.freedesktop.Akonadi.Resource.{instance_id}.{self._instance_id}"

    def agent_service_name(self, instance_id: str) -> str:
        return f"org.freedesktop.Akonadi.Agent.{instance_id}.{self._instance_id}"

    @property
    def control_interface(self) -> OrgFreedesktopAkonadiControlManagerInterface:
        return OrgFreedesktopAkonadiControlManagerInterface(
            self.akonadi_control_service_name,
            "/ControlManager",
        )

    @property
    def server_interface(self) -> OrgFreedesktopAkonadiServerInterface:
        return OrgFreedesktopAkonadiServerInterface(
            self.akonadi_server_service_name,
            "/Server",
        )

    @property
    def agent_manager_interface(self) -> OrgFreedesktopAkonadiAgentManagerInterface:
        return OrgFreedesktopAkonadiAgentManagerInterface(
            self.akonadi_control_service_name,
            "/AgentManager",
        )

    def agent_interface(self, instance_name: str) -> OrgFreedesktopAkonadiAgentControlInterface:
        return OrgFreedesktopAkonadiAgentControlInterface(
            self.agent_service_name(instance_name),
            "/",
        )

    def resource_interface(self, instance_name: str) -> OrgFreedesktopAkonadiResourceInterface:
        return OrgFreedesktopAkonadiResourceInterface(
            self.resource_service_name(instance_name),
            "/",
        )

    def name_owner(self, service_name: str) -> str:
        log.debug("Waiting for name owner of %s", service_name)
        dbus = FreedesktopDbus(
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
        )

        if not dbus.name_has_owner(service_name):
            log.debug("Service %s has no owner, waiting for it...", service_name)
            wait_until(lambda: dbus.name_has_owner(service_name))
            owner = dbus.get_name_owner(service_name)
            log.debug("Name owner changed: %s -> %s", service_name, owner)
        else:
            owner = dbus.get_name_owner(service_name)
            log.debug("Service %s has owner %s, continuing", service_name, owner)

        assert owner is not None
        return owner

    def wait_name_owner_changed(self, name_owner: str, service_name: str, timeout=5):
        def name_owner_changed() -> bool:
            new_owner = self.name_owner(service_name)
            return new_owner != name_owner

        wait_until(name_owner_changed, timeout=timeout)
