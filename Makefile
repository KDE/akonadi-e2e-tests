.PHONY: docker init bindings

ALL: init docker

init:
	uv venv --system-site-packages
	uv sync

bindings:
	# TODO: once akonadi bindings merged in master, remove --no-src
	kde-builder --no-src --no-include-dependencies akonadi

test:
	uv run pytest

docker:
	make -C docker
