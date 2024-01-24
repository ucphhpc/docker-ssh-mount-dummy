PACKAGE_NAME=ssh-mount-dummy
PACKAGE_NAME_FORMATTED=$(subst -,_,$(PACKAGE_NAME))
OWNER=ucphhpc
IMAGE=$(PACKAGE_NAME)
# Enable that the builder should use buildkit
# https://docs.docker.com/develop/develop-images/build_enhancements/
DOCKER_BUILDKIT=1
# NOTE: dynamic lookup with docker as default and fallback to podman
DOCKER = $(shell which docker || which podman)
# if compose is not found, try to use it as plugin
DOCKER_COMPOSE = $(shell which docker-compose || which podman-compose || echo 'docker compose')
$(echo ${DOCKER_COMPOSE} >/dev/null)
TAG=edge
ARGS=

.PHONY: all init dockerbuild dockerclean dockerpush clean dist distclean maintainer-clean
.PHONY: install uninstall installcheck check

all: venv install-dep init dockerbuild

init:
ifeq ($(shell test -e defaults.env && echo yes), yes)
ifneq ($(shell test -e .env && echo yes), yes)
		ln -s defaults.env .env
endif
endif
	mkdir -p authorized-keys
	. $(VENV)/activate; python3 init-images.py

dockerbuild:
	$(DOCKER_COMPOSE) build $(ARGS)

dockerclean:
	$(DOCKER) rmi -f $(OWNER)/$(IMAGE):$(TAG)

dockerpush:
	$(DOCKER) push $(OWNER)/$(IMAGE):$(TAG)

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

clean:
	$(MAKE) dockerclean
	$(MAKE) distclean
	$(MAKE) venv-clean
	rm -fr authorized-keys
	rm -fr .env
	rm -fr .pytest_cache
	rm -fr tests/__pycache__

dist:
### PLACEHOLDER ###

distclean:
### PLACEHOLDER ###

maintainer-clean:
	@echo 'This command is intended for maintainers to use; it'
	@echo 'deletes files that may need special tools to rebuild.'
	$(MAKE) distclean

install-dep:
	$(VENV)/pip install -r requirements.txt

install:
	$(MAKE) install-dep

uninstall:
	$(VENV)/pip uninstall -y -r requirements.txt

uninstallcheck:
	$(VENV)/pip uninstall -y -r tests/requirements.txt

installcheck:
	$(VENV)/pip install -r tests/requirements.txt

check:
	. $(VENV)/activate; pytest -s -v tests/

include Makefile.venv
