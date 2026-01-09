# PyAccess Publishing Makefile

.PHONY: build test publish publish-test clean

# Build the package
build:
	uv build

# Run tests
test:
	uv run pytest

# Publish to Test PyPI
publish-test: build
	uv publish --publish-url https://test.pypi.org/legacy/ --token $(shell cat .pypi_token)

# Publish to production PyPI
publish: build
	uv publish --token $(shell cat .pypi_token)

# Clean build artifacts
clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Full test and publish to test PyPI
test-publish: test publish-test

# Help
help:
	@echo "Available targets:"
	@echo "  build        - Build the package"
	@echo "  test         - Run tests"
	@echo "  publish-test - Build and publish to Test PyPI"
	@echo "  publish      - Build and publish to production PyPI"
	@echo "  test-publish - Run tests, build and publish to Test PyPI"
	@echo "  clean        - Clean build artifacts"
	@echo "  help         - Show this help"
	@echo ""
	@echo "Make sure to put your PyPI API token in .pypi_token file"