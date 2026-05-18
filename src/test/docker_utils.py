# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
#
# SPDX-License-Identifier: GPL-2.0-or-later

from os import environ


def get_image_name(image: str) -> str:
    return f"{environ.get('DOCKER_IMAGE_PREFIX', 'akonadi-e2e-')}{image}:latest"
