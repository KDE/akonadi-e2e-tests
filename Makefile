.PHONY: docker init bindings test lint

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

lint:
	uv run pytest --ignore-glob='test_*.py' --ignore-glob='*_test.py' --ignore-glob='tests/*' --ruff --ruff-format --mypy
