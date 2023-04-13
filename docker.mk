PLUGINNAME = PreCourlis
LOCALES = fr

TS_FILES = $(addprefix $(PLUGINNAME)/i18n/, $(addsuffix .ts, $(LOCALES)))
QM_FILES = $(addprefix $(PLUGINNAME)/i18n/, $(addsuffix .qm, $(LOCALES)))

SOURCES := $(shell find $(PLUGINNAME) -path $(PLUGINNAME)/lib -prune -false -o -name "*.py" -o -name "*.ui")

default: help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    %-20s%s\n", $$1, $$2}'


#########
# Build #
#########

build: ## Build all runtime files
build: transcompile
	make -C $(PLUGINNAME)/resources
	make -C $(PLUGINNAME)/lib
	# make -C help html

.PHONY: transcompile
transcompile: $(QM_FILES)


.PHONY: transup
transup: ## Update translation files with any new strings.
transup: $(TS_FILES)

$(PLUGINNAME)/i18n/%.ts: $(SOURCES)
	pylupdate5 -verbose -noobsolete $(SOURCES) -ts $@

$(PLUGINNAME)/i18n/%.qm: $(PLUGINNAME)/i18n/%.ts
	lrelease $<


########
# Lint #
########

.PHONY: check
check: ## Run all linters
check: black-check flake8

.PHONY: black
black:
	black $(PLUGINNAME) test

.PHONY: black-check
black-check:
	black --check $(PLUGINNAME) test

.PHONY: flake8
flake8:
	flake8 $(PLUGINNAME) test


#########
# Tests #
#########

.PHONY: nosetests
nosetests: ## Run tests using nose
	nosetests -v --with-id --with-coverage --cover-package=. ${NOSETESTS_ARGS}

.PHONY: pytest
pytest:  ## Run tests using pytest
	pytest --cov --verbose --color=yes ${PYTEST_ARGS}

.PHONY: coverage
coverage: ## Display coverage report
	coverage report -m
