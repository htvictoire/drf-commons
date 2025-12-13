.PHONY: help install install-dev clean lint format sort-imports type-check quality test test-verbose coverage build upload upload-test publish publish-test clean-build clean-pyc clean-test all check

# Default target
help:
	@echo "Available commands:"
	@echo "  help          Show this help message"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install       Install package"
	@echo "  install-dev   Install package with development dependencies"
	@echo "  clean         Clean all build artifacts and cache"
	@echo ""
	@echo "Code Quality:"
	@echo "  format        Format code with black"
	@echo "  sort-imports  Sort imports with isort"
	@echo "  lint          Run flake8 linting"
	@echo "  type-check    Run mypy type checking"
	@echo "  quality       Run all code quality checks (format, sort-imports, lint, type-check)"
	@echo ""
	@echo "Testing:"
	@echo "  test          Run tests"
	@echo "  test-verbose  Run tests with verbose output"
	@echo "  coverage      Run tests with coverage report"
	@echo ""
	@echo "Build & Release:"
	@echo "  build         Build distribution packages"
	@echo "  upload        Upload to PyPI (requires credentials)"
	@echo "  upload-test   Upload to TestPyPI (requires credentials)"
	@echo "  publish       Alias for upload"
	@echo "  publish-test  Clean, build, and publish to TestPyPI"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean-build   Clean build artifacts"
	@echo "  clean-pyc     Clean Python file artifacts"
	@echo "  clean-test    Clean test artifacts"
	@echo ""
	@echo "Combined:"
	@echo "  all           Install, run quality checks, test, and build"
	@echo "  check         Run quality checks and tests (CI-friendly)"

# Setup & Installation
install:
	pip install -e .

install-dev:
	pip install -e .[dev,test,build,all]
	@echo "Development environment ready!"

# Code Quality
format:
	@echo "Formatting code with black..."
	black . --exclude="venv|.venv|env|.env"
	@echo "✓ Code formatted"

sort-imports:
	@echo "Sorting imports with isort..."
	isort . --skip-glob="venv/*" --skip-glob=".venv/*" --skip-glob="env/*" --skip-glob=".env/*"
	@echo "✓ Imports sorted"

lint:
	@echo "Running flake8 linting..."
	flake8 . --exclude=venv,.venv,env,.env
	@echo "✓ Linting passed"

type-check:
	@echo "Running mypy type checking..."
	mypy . --exclude="venv|.venv|env|.env"
	@echo "✓ Type checking passed"

quality: format sort-imports lint type-check
	@echo "✓ All code quality checks passed"

# Testing
test:
	@echo "Running tests..."
	@if [ -n "$(filter-out test,$(MAKECMDGOALS))" ]; then \
		TEST_ARG="$(filter-out test,$(MAKECMDGOALS))"; \
		BASE_PATH=$$(echo "$$TEST_ARG" | sed 's/\./\//g'); \
		if echo "$$TEST_ARG" | grep -q "test_"; then \
			PACKAGE_PATH=$$(echo "$$BASE_PATH" | sed 's/\/test_.*//' ); \
			TEST_FILE=$$(echo "$$BASE_PATH" | sed 's/.*\///' ); \
			if [ -f "$$PACKAGE_PATH/tests/$$TEST_FILE.py" ]; then \
				DJANGO_SETTINGS_MODULE=drf_commons.common_conf.django_settings python -m pytest "$$PACKAGE_PATH/tests/$$TEST_FILE.py"; \
			else \
				echo "Error: $$PACKAGE_PATH/tests/$$TEST_FILE.py not found"; exit 1; \
			fi; \
		elif [ -d "$$BASE_PATH/tests" ] && [ -n "$$(find "$$BASE_PATH/tests" -name "test_*.py" -o -name "*_test.py" | head -1)" ]; then \
			DJANGO_SETTINGS_MODULE=drf_commons.common_conf.django_settings python -m pytest "$$BASE_PATH/"; \
		elif [ -d "$$BASE_PATH" ]; then \
			DJANGO_SETTINGS_MODULE=drf_commons.common_conf.django_settings python -m pytest "$$BASE_PATH/"; \
		else \
			echo "Error: $$BASE_PATH not found"; exit 1; \
		fi; \
	else \
		DJANGO_SETTINGS_MODULE=drf_commons.common_conf.django_settings python -m pytest; \
	fi
	@echo "✓ Tests passed"

%:
	@:

test-verbose:
	@echo "Running tests with verbose output..."
	DJANGO_SETTINGS_MODULE=drf_commons.common_conf.django_settings python -m pytest -v
	@echo "✓ Tests passed"

coverage:
	@echo "Running tests with coverage..."
	DJANGO_SETTINGS_MODULE=drf_commons.common_conf.django_settings python -m pytest --cov=drf_commons --cov-report=html --cov-report=term
	@echo "✓ Coverage report generated"

# Build & Release
build: clean-build
	@echo "Building distribution packages..."
	python setup.py sdist bdist_wheel
	@echo "✓ Build completed"

upload: build
	@echo "Uploading to PyPI..."
	twine upload dist/*
	@echo "✓ Uploaded to PyPI"

upload-test: build
	@echo "Uploading to TestPyPI..."
	twine upload --repository testpypi dist/*
	@echo "✓ Uploaded to TestPyPI"

# Aliases for publishing
publish: upload
	@echo "✓ Published to PyPI"

publish-test: clean-build
	@echo "Cleaning build artifacts..."
	@echo "Building distribution packages..."
	python -m build
	@echo "Uploading to TestPyPI..."
	twine upload --repository testpypi dist/*
	@echo "✓ Published to TestPyPI"

# Cleaning
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache/
	rm -fr .mypy_cache/

clean: clean-build clean-pyc clean-test
	@echo "✓ All artifacts cleaned"

# Combined targets
all: install-dev quality test build
	@echo "✓ Complete pipeline finished successfully!"

check: quality test
	@echo "✓ All checks passed - ready for CI/CD"