DOCKER_NAME_PREFIX = akonadi-e2e

ALL: build-cyrus build-dovecot build-nextcloud build-radicale

build-%:
	cd "$*" && docker build -t "${DOCKER_NAME_PREFIX}-$*" .
