# SPDX-FileCopyrightText: 2025 Daniel Vrátil <dvratil@kde.org>
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os
from pathlib import Path


class AkonadiEnv:
    """Describes the environment for the Akonadi server.

    Returns paths to various configuration files and directories.
    """

    def __init__(self, root_path: Path, instance_id: str) -> None:
        self._root_path = root_path
        self._instance_id = instance_id

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def home_dir(self) -> Path:
        return self._root_path / "home"

    @property
    def xdg_config_home(self) -> Path:
        return self._root_path / "config"

    @property
    def xdg_cache_home(self) -> Path:
        return self._root_path / "cache"

    @property
    def tmp_dir(self) -> Path:
        return self._root_path / "tmp"

    @property
    def xdg_data_home(self) -> Path:
        return self._root_path / "data"

    @property
    def akonadi_config_dir(self) -> Path:
        return self.xdg_config_home / "akonadi/instance" / self._instance_id

    @property
    def akonadi_data_dir(self) -> Path:
        return self.xdg_data_home / "akonadi/instance" / self._instance_id

    @property
    def akonadiserverrc_path(self) -> Path:
        return self.akonadi_config_dir / "akonadiserverrc"

    @property
    def db_path(self) -> Path:
        return self.akonadi_data_dir / "akonadi.db"

    @property
    def environ(self) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home_dir)
        env["TMPDIR"] = str(self.tmp_dir)
        env["XDG_CONFIG_HOME"] = str(self.xdg_config_home)
        env["XDG_CACHE_HOME"] = str(self.xdg_cache_home)
        env["XDG_DATA_HOME"] = str(self.xdg_data_home)
        env["AKONADI_INSTANCE"] = self._instance_id
        env["AKONADI_DISABLE_AGENT_AUTOSTART"] = "true"
        env["LC_ALL"] = "C"
        env["QT_LOGGING_RULES"] = ";".join(
            [
                "kf.dav=true",
                "org.kde.pim.kimap=true",
                "org.kde.pim.akonadi=true",
                "org.kde.pim.akonadiagentbase=true",
                "org.kde.pim.akonadiserver=true",
                "org.kde.pim.akonadicore=true",
                "org.kde.pim.akonadiprivate=true",
                "org.kde.pim.davresource=true",
                "org.kde.pim.imapresource=true",
                "org.kde.pim.imapresource.trace=true",
            ]
        )
        if "QT_MESSAGE_PATTERN" not in env:
            env["QT_MESSAGE_PATTERN"] = "FOOO %{category} %{type}: %{function} - %{message}"

        return env
