#/***************************************************************************
# PreCourlisPlugin
#
# Creation de profils pour Courlis

#        begin              : 2020-03-13
#        git sha            : $Format:%H$
#        copyright          : (C) 2020 by EDF Hydro, DeltaCAD, Camptocamp
#        email              : matthieu.secher@edf.fr
# ***************************************************************************/

#/***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************/


###########################################################
# This variables may be overriden to match you environment
###########################################################

# If locales are enabled, set the name of the lrelease binary on your system. If
# you have trouble compiling the translations, you may have to specify the full path to
# lrelease
#LRELEASE = lrelease
#LRELEASE = lrelease-qt4

# QGISDIR points to the location where your plugin should be installed.
# This varies by platform, relative to your HOME directory:
# * Linux:
#   .local/share/QGIS/QGIS3/profiles/default/python/plugins/
# * Mac OS X:
#   Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins
# * Windows:
#   AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins'
QGISDIR ?= .local/share/QGIS/QGIS3/profiles/default

###############################################################
# Normally you would not need to override variables below here
###############################################################

PLUGINNAME = PreCourlis
LOCALES = fr

DOCKER_RUN_CMD = docker-compose run --rm --user `id -u` builder

toto:
	@echo $(SOURCES)

default: help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    %-20s%s\n", $$1, $$2}'

.PHONY: docker-build
docker-build:
	docker build --target test --tag camptocamp/edf-precourlis-builder ./docker

.PHONY: build
build: ## Compile resources and help files
build: docker-build
	$(DOCKER_RUN_CMD) make -f docker.mk build

.PHONY: clean
clean: ## Delete generated files
	rm -rf .pytest_cache
	rm -rf help/build
	rm -f $(PLUGINNAME)/i18n/*.qm
	rm -f $(PLUGINNAME)/ui/resources_rc.py
	rm -f .coverage .noseids
	rm -f PreCoulis.zip

.PHONY: check
check: ## Run linters
	$(DOCKER_RUN_CMD) make -f docker.mk check

.PHONY: black
black: ## Run black formatter
	$(DOCKER_RUN_CMD) make -f docker.mk black

.PHONY: test
test: ## Run the automated tests suite
test:
	$(DOCKER_RUN_CMD) make -f docker.mk pytest

.PHONY: bash
bash: ## Run bash in tests container
	$(DOCKER_RUN_CMD) bash

.PHONY: transup
transup: ## Update translation files with any new strings.
	$(DOCKER_RUN_CMD) make -f docker.mk transup


deploy: ## Deploy plugin to your QGIS plugin directory (to test zip archive)
deploy: package derase
	unzip PreCourlis.zip -d $(HOME)/$(QGISDIR)/python/plugins/

derase: ## Remove deployed plugin from your QGIS plugin directory
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

package: ## Create a zip package of the plugin named $(PLUGINNAME).zip.
package: compile
	rm -f $(PLUGINNAME).zip
	git archive -o $(PLUGINNAME).zip HEAD $(PLUGINNAME)
	echo "Created package: $(PLUGINNAME).zip"

.PHONY: upload
upload: ## Upload plugin to QGIS Plugin repo
upload: package
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip


.PHONY: link
link: ## Create symbolic link to this folder in your QGIS plugins folder (for development)
link: derase
	ln -s $(shell pwd)/$(PLUGINNAME) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

.PHONY: unlink
unlink: ## Unlink $(PLUGINNAME) in your QGIS plugins folder
unlink: derase
