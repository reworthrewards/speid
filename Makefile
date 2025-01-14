SHELL := bash
PROJECT = speid
PYTHON = python3.8
DOCKER = docker-compose run --rm $(PROJECT)
isort = isort $(PROJECT) tests
black = black -S -l 79 --target-version py37 $(PROJECT) tests

default: install

install:
	pip install -q -r requirements.txt

install-dev:
	$(MAKE) install
	pip install -q -r requirements-dev.txt

venv:
	$(PYTHON) -m venv --prompt $(PROJECT) venv
	./venv/bin/pip install -qU pip

format:
	$(isort)
	$(black)

lint:
	flake8 $(PROJECT) tests
	$(isort) --check-only
	$(black) --check
	mypy $(PROJECT)

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist

test: clean lint
	pytest --cov-report term-missing tests/ --cov=speid


ci-test:
	$(MAKE) install-dev
	$(MAKE) lint
	$(MAKE) docker-build
	$(DOCKER) scripts/test.sh

docker-test: docker-build
	# Clean up even if there's an error
	$(DOCKER) scripts/test.sh || $(MAKE) docker-stop
	$(MAKE) docker-stop

docker-build: clean
	docker-compose build
	touch docker-build

docker-stop:
	docker-compose stop
	docker-compose rm -f

clean-docker:
	docker-compose down --rmi local
	rm docker-build

docker-shell: docker-build
	# Clean up even if there's an error
	$(DOCKER) scripts/devwrapper.sh bash || $(MAKE) docker-stop
	$(MAKE) docker-stop


.PHONY: install install-dev lint clean-pyc test docker-stop clean-docker shell
