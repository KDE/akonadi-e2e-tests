# SPDX-FileCopyrightText: Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-License-Identifier: GPL-2.0-or-later

CONTAINER_RUNTIME ?= docker
IMAGE_NAME_PREFIX ?= akonadi-e2e-
IMAGE_TAG ?= latest
TARGETS := cyrus dovecot nextcloud radicale

.PHONY: all $(TARGETS)

all: $(TARGETS)

$(TARGETS):
	cd "$@" && ${CONTAINER_RUNTIME} build --pull --no-cache --tag "${IMAGE_NAME_PREFIX}$@:${IMAGE_TAG}" .
