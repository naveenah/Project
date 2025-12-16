# Makefile for managing dependencies with pip-tools

.PHONY: help compile sync install install-dev upgrade clean

REQUIREMENTS_DIR = src/requirements
PROD_IN = $(REQUIREMENTS_DIR)/requirements-prod.in
DEV_IN = $(REQUIREMENTS_DIR)/requirements-dev.in
PROD_TXT = $(REQUIREMENTS_DIR)/requirements-prod.txt
DEV_TXT = $(REQUIREMENTS_DIR)/requirements-dev.txt

help:
	@echo "Available commands:"
	@echo "  make compile       - Compile production and development requirements files"
	@echo "  make sync          - Sync environment with production requirements only"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make upgrade       - Upgrade all dependencies to latest versions"
	@echo "  make clean         - Remove compiled requirements files"

compile:
	pip-compile --resolver=backtracking $(PROD_IN) -o $(PROD_TXT)
	pip-compile --resolver=backtracking $(DEV_IN) -o $(DEV_TXT)

sync:
	pip-sync $(PROD_TXT)

install:
	pip install -r $(PROD_TXT)

install-dev:
	pip install -r $(PROD_TXT) -r $(DEV_TXT)

upgrade:
	pip-compile --upgrade --resolver=backtracking $(PROD_IN) -o $(PROD_TXT)
	pip-compile --upgrade --resolver=backtracking $(DEV_IN) -o $(DEV_TXT)

clean:
	rm -f $(PROD_TXT) $(DEV_TXT)
