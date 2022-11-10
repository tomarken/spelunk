PACKAGE = spelunk

# the location of the venv
VENV_LOC ?= .venv

.PHONY: install-repo
install-repo: # Creates a venv using PYTHON_EXEC (can be set externally to not use pyenv)
	    source $(VENV_LOC)/bin/activate; \
	    poetry install --remove-untracked; \
	    deactivate


.PHONY: unit-test
unit-test:
	    poetry run pytest --cov-report term-missing --cov=$(PACKAGE) tests


.PHONY: style-check
style-check:
	    poetry run black --check --verbose --diff --color $(PACKAGE) tests


.PHONY: reformat
reformat:
	    poetry run black $(PACKAGE) tests


.PHONY: lint
lint:
	    poetry run flake8 $(PACKAGE) tests
