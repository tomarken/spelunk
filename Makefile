PACKAGE = spelunk

# URLs for various installers needed during bootstrapping
INSTALLER_URL_PYENV = https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer
INSTALLER_URL_POETRY = https://install.python-poetry.org

# the pyenv installation must be here unless set externally
PYENV_ROOT ?= ~/.pyenv
# the pyenv binary to use
PYENV_BIN ?= $(PYENV_ROOT)/bin/pyenv
# the version of Python to install with pyenv
PYTHON_VERSION ?= 3.9.15
# the venv prompt name
VENV_NAME ?= spelunk
# the location to install the venv
VENV_LOC ?= .venv


.PHONY: install-python
install-python: # installs pyenv if not present and then uses PYENV_BIN to install the specified version if it doesn't exist
	    @($(PYENV_BIN) --version) || (curl -L $(INSTALLER_URL_PYENV) | bash)
	    @$(PYENV_BIN) install --skip-existing $(PYTHON_VERSION)


.PHONY: install-poetry
install-poetry: # installs the Poetry package manager if not installed using PYTHON_EXEC
	    @($$(which poetry) --version) || (export PYTHON_EXEC=$$($(PYENV_BIN) prefix $(PYTHON_VERSION))/bin/python; \
	    curl -sSL $(INSTALLER_URL_POETRY) | $$PYTHON_EXEC - --version 1.1.15)


.PHONY: install-repo
install-repo: # Creates a venv using PYTHON_EXEC (can be set externally to not use pyenv)
	    @export PYTHON_EXEC=$$($(PYENV_BIN) prefix $(PYTHON_VERSION))/bin/python; \
	    if [ -f $(VENV_LOC)/bin/python ] && [ -f $(VENV_LOC)/bin/activate ]; then echo "venv already created"; else ($$PYTHON_EXEC -m venv $(VENV_LOC) --prompt $(VENV_NAME)); fi
	    source $(VENV_LOC)/bin/activate; \
	    poetry install --remove-untracked; \
	    deactivate


.PHONY: unit-test
unit-test:
	    poetry run pytest --cov-report term-missing --cov=$(PACKAGE) tests


.PHONY: style-check
style-check:
	    poetry run black --check --verbose --diff --color $(PACKAGE) tests


.PHONY: format
format:
	    poetry run black $(PACKAGE) tests


.PHONY: lint
lint:
	    poetry run flake8 $(PACKAGE) tests
