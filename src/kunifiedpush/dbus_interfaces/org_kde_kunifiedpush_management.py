# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from sdbus import (
    DbusInterfaceCommon,
    DbusUnprivilegedFlag,
    dbus_method,
)


class OrgKdeKunifiedpushManagement(
    DbusInterfaceCommon,
    interface_name="org.kde.kunifiedpush.Management",
):
    @dbus_method(
        flags=DbusUnprivilegedFlag, method_name="registeredClients", result_signature="a(sss)"
    )
    def registered_clients(self) -> list[tuple[str, str, str]]:
        raise NotImplementedError
