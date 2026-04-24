# SPDX-FileCopyrightText: Dominique MICHEL <dominique.michel@enioka.com>
# SPDX-License-Identifier: GPL-2.0-or-later

.PHONY: all docker init test lint

all: init docker

init:
	uv venv --system-site-packages --python $(shell which python3)
	uv sync

test:
	uv run pytest

docker:
	make -C docker

lint:
	uv run pytest -k "ruff or mypy" --ruff --ruff-format --mypy
