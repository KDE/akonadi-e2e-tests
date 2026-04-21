# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from src.imap.imap_server import ImapServer

log = getLogger(__name__)


class DovecotServer(ImapServer):
    # Default user created by the image
    DOCKER_IMAGE = "akonadi-e2e-dovecot:latest"
    USERNAME = "admin"
    PASSWORD = "admin"
    CONTAINER_NAME = "dovecot-akonadi-e2e-tests"
    DELIMITER = "."
