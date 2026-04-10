DOCKER_NAME_PREFIX = akonadi-e2e
TARGETS := cyrus dovecot nextcloud radicale

.PHONY: all $(TARGETS)

all: $(TARGETS)

$(TARGETS):
	cd "$@" && docker build -t "${DOCKER_NAME_PREFIX}-$@" .
