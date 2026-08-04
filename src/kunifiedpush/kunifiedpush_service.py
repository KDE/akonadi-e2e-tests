# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import subprocess
import time
from functools import cached_property
from logging import getLogger
from pathlib import Path
from textwrap import dedent

from src.akonadi.env import AkonadiEnv
from src.kunifiedpush.dbus_interfaces.org_kde_kunifiedpush_management import (
    OrgKdeKunifiedpushManagement,
)
from src.kunifiedpush.dbus_interfaces.org_unifiedpush_distributor2 import (
    OrgUnifiedpushDistributor2Interface,
)
from src.ntfy.ntfy_server import NtfyServer

log = getLogger(__name__)


class KunifiedPushService:
    def __init__(self, akonadi_env: AkonadiEnv, ntfy_server: NtfyServer):
        self.env = akonadi_env.environ
        self.service_name = f"org.unifiedpush.Distributor.{akonadi_env.instance_id}"
        self.write_ntfy_config(
            akonadi_env.xdg_config_home / "KDE",
            f"http://{ntfy_server.host_or_ip}:{ntfy_server.port}/",
        )

    def start(self) -> None:
        self.subprocess = subprocess.Popen(
            ["kunifiedpush-distributor"],
            env=self.env,
        )
        self.management_interface = OrgKdeKunifiedpushManagement(self.service_name, "/Management")
        self.distributor_interface = OrgUnifiedpushDistributor2Interface(
            self.service_name, "/Management"
        )
        self.wait_ready()

    def stop(self) -> None:
        self.subprocess.kill()

    @cached_property
    def service_name(self) -> str:
        return self.service_name

    def registered_clients(self) -> list[tuple[str, str, str]]:
        return self.management_interface.registered_clients()

    def register(self, token: str) -> dict[str, tuple]:
        register_args = {
            "service": ("s", self.service_name),
            "token": ("s", token),
        }
        return self.distributor_interface.register(register_args)

    def unregister(self, token: str) -> dict[str, tuple]:
        unregister_args = {"token": ("s", token)}
        return self.distributor_interface.unregister(unregister_args)

    def wait_ready(self) -> None:
        for _ in range(100):
            try:
                self.management_interface.registered_clients()
                return
            except Exception:
                time.sleep(0.1)

        raise TimeoutError("kunifiedpush distributor failed to get ready in time")

    def write_ntfy_config(self, config_path: Path, ntfy_url: str):
        print(config_path)
        config_path.mkdir(exist_ok=True)
        with open(config_path / "kunifiedpush-distributor.conf", "w", encoding="utf-8") as f:
            f.write(
                dedent(f"""[Clients]
Tokens=@Invalid()

[Ntfy]
AuthMethod=None
Secret=
Url={ntfy_url}
Username=

[Ntfy-internal]
LastMessageId=
Topics=@Invalid()

[PushProvider]
Type=Ntfy
""")
            )
