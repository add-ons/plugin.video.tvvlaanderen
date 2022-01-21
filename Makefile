export KODI_HOME := $(CURDIR)/tests/home
export KODI_INTERACTIVE := 0
PYTHON := python

# Collect information to build as sensible package name
name = $(shell xmllint --xpath 'string(/addon/@id)' addon.xml)

languages = $(filter-out en_gb, $(patsubst resources/language/resource.language.%, %, $(wildcard resources/language/*)))

all: check test build
zip: build
multizip: build

check: check-pylint check-translations

check-pylint:
	@printf ">>> Running pylint checks\n"
	@$(PYTHON) -m pylint *.py resources/lib/ tests/

check-translations:
	@printf ">>> Running translation checks\n"
	@$(foreach lang,$(languages), \
		msgcmp resources/language/resource.language.$(lang)/strings.po resources/language/resource.language.en_gb/strings.po; \
	)
	@tests/check_for_unused_translations.py

check-addon: clean build
	@printf ">>> Running addon checks\n"
	$(eval TMPDIR := $(shell mktemp -d))
	@unzip dist/plugin.video.m7group-*+matrix.1.zip -d ${TMPDIR}
	cd ${TMPDIR} && kodi-addon-checker --branch=matrix
	@rm -rf ${TMPDIR}

codefix:
	@isort -l 160 resources/

test:
	@printf ">>> Running unit tests\n"
	@$(PYTHON) -m pytest tests

clean:
	@printf ">>> Cleaning up\n"
	@find . -name '*.py[cod]' -type f -delete
	@find . -name '__pycache__' -type d -delete
	@rm -rf .pytest_cache/ tests/cdm tests/userdata/temp
	@rm -f *.log .coverage
	@rm -rf dist/

build: clean
	@printf ">>> Building generic base add-on\n"
	@scripts/build.py base

brands: clean
	@printf ">>> Building all branded add-ons\n"
	@scripts/build.py brands

release:
ifneq ($(release),)
	@github_changelog_generator -u add-ons -p $(name) --no-issues --exclude-labels duplicate,question,invalid,wontfix,release --future-release v$(release);

	@printf "cd /addon/@version\nset $$release\nsave\nbye\n" | xmllint --shell addon.xml; \
	date=$(shell date '+%Y-%m-%d'); \
	printf "cd /addon/extension[@point='xbmc.addon.metadata']/news\nset v$$release ($$date)\nsave\nbye\n" | xmllint --shell addon.xml; \

	# Next steps to release:
	# - Modify the news-section of addons.xml
	# - git add . && git commit -m "Prepare for v$(release)" && git push
	# - git tag v$(release) && git push --tags
else
	@printf "Usage: make release release=1.0.0\n"
endif

.PHONY: brands