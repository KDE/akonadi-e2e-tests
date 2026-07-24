# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgUnifiedpushDistributor2Interface(
    DbusInterfaceCommon,
    interface_name="org.unifiedpush.Distributor2",
):
    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="Register",
        input_signature="a{sv}",
        result_signature="a{sv}",
    )
    def register(self, args: dict[str, tuple]) -> dict[str, tuple]:
        raise NotImplementedError

    @dbus_method(
        flags=DbusUnprivilegedFlag,
        method_name="Unregister",
        input_signature="a{sv}",
        result_signature="a{sv}",
    )
    def unregister(self, args: dict[str, tuple]) -> dict[str, tuple]:
        raise NotImplementedError
