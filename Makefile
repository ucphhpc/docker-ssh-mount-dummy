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

.PHONY: all
all: venv install-dep init dockerbuild

.PHONY: init
init:
ifeq ($(shell test -e defaults.env && echo yes), yes)
ifneq ($(shell test -e .env && echo yes), yes)
		ln -s defaults.env .env
endif
endif
	mkdir -p authorized-keys mnt
	. $(VENV)/activate; python3 init-images.py

.PHONY: dockerbuild
dockerbuild:
	$(DOCKER_COMPOSE) build $(ARGS)

.PHONY: dockerclean
dockerclean:
	$(DOCKER) rmi -f $(OWNER)/$(IMAGE):$(TAG)

.PHONY: dockerpush
dockerpush:
	$(DOCKER) push $(OWNER)/$(IMAGE):$(TAG)

.PHONY: up
up:
	$(DOCKER_COMPOSE) up -d

.PHONY: down
down:
	$(DOCKER_COMPOSE) down

.PHONY: clean
clean:
	$(MAKE) dockerclean
	$(MAKE) distclean
	$(MAKE) venv-clean
	rm -fr authorized-keys
	rm -fr mnt
	rm -fr .env
	rm -fr .pytest_cache
	rm -fr tests/__pycache__


.PHONY: dist
dist:
### PLACEHOLDER ###

.PHONY: distclean
distclean:
### PLACEHOLDER ###

.PHONY: maintainer-clean
maintainer-clean:
	@echo 'This command is intended for maintainers to use; it'
	@echo 'deletes files that may need special tools to rebuild.'
	$(MAKE) distclean

.PHONY: install-dev
install-dev:
	$(VENV)/pip install -r requirements-dev.txt

.PHONY: uninstall-dev
uninstall-dev:
	$(VENV)/pip uninstall -y -r requirements-dev.txt

.PHONY: install-dep
install-dep:
	$(VENV)/pip install -r requirements.txt

.PHONY: install
install:
	$(MAKE) install-dep

.PHONY: uninstall
uninstall:
	$(VENV)/pip uninstall -y -r requirements.txt

.PHONY: uninstalltest
uninstalltest:
	$(VENV)/pip uninstall -y -r tests/requirements.txt

.PHONY: installtest
installtest:
	$(VENV)/pip install -r tests/requirements.txt

.PHONY: test
test:
	. $(VENV)/activate; pytest -s -v tests/

include Makefile.venv
