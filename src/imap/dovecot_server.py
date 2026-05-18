# SPDX-FileCopyrightText: 2026 Noham Devillers <nde@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from logging import getLogger

from src.imap.imap_server import ImapServer
from src.test.docker_utils import get_image_name

log = getLogger(__name__)


class DovecotServer(ImapServer):
    DOCKER_IMAGE = get_image_name("dovecot")
    # Default user created by the image
    USERNAME = "admin"
    PASSWORD = "admin"
    CONTAINER_NAME = "dovecot-akonadi-e2e-tests"
    DELIMITER = "."
