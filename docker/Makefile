# SPDX-FileCopyrightText: Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-License-Identifier: GPL-2.0-or-later

CONTAINER_RUNTIME ?= docker
IMAGE_NAME_PREFIX ?= akonadi-e2e-
IMAGE_TAG ?= latest
TARGETS := cyrus dovecot radicale

.PHONY: all $(TARGETS) nextcloud nextcloud-push-notifications

all: $(TARGETS) nextcloud nextcloud-push-notifications

$(TARGETS):
	cd "$@" && ${CONTAINER_RUNTIME} build --pull --no-cache --tag "${IMAGE_NAME_PREFIX}$@:${IMAGE_TAG}" .

nextcloud:
	cd "$@" && ${CONTAINER_RUNTIME} build --pull --no-cache --target base_nextcloud --tag "${IMAGE_NAME_PREFIX}$@:${IMAGE_TAG}" .

nextcloud-push-notifications:
	cd "nextcloud" && ${CONTAINER_RUNTIME} build --pull --no-cache --target nextcloud_push --tag "${IMAGE_NAME_PREFIX}nextcloud-push-notifications:${IMAGE_TAG}" .
