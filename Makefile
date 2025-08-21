# Whisper Transcriber Makefile
# ============================

# Variables
PYTHON := python3
PIP := pip3
VENV_DIR := .venv
APP_NAME := whisper-transcriber
VERSION := $(shell grep version setup.py | cut -d'"' -f2 || echo "1.0.0")

# Platform detection
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM := macos
endif
ifeq ($(OS),Windows_NT)
    PLATFORM := windows
endif

# Colors for output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

.PHONY: help install clean dev-install test build build-all package docker ci-setup

# Default target
help: ## Show this help message
	@echo "$(BLUE)Whisper Transcriber Build System$(NC)"
	@echo "=================================="
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip setuptools wheel
	$(VENV_DIR)/bin/pip install -r requirements.txt

dev-install: install ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(VENV_DIR)/bin/pip install -r requirements-dev.txt

# Development targets
clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf __pycache__/ */__pycache__/ */*/__pycache__/
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(VENV_DIR)/bin/python -m pytest tests/ -v --cov=src --cov-report=html

lint: ## Run code linting
	@echo "$(BLUE)Running linters...$(NC)"
	$(VENV_DIR)/bin/flake8 src/ main.py
	$(VENV_DIR)/bin/black --check src/ main.py
	$(VENV_DIR)/bin/isort --check-only src/ main.py

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	$(VENV_DIR)/bin/black src/ main.py
	$(VENV_DIR)/bin/isort src/ main.py

# Build targets
build: clean ## Build for current platform
	@echo "$(BLUE)Building for $(PLATFORM)...$(NC)"
	$(VENV_DIR)/bin/pip install pyinstaller
	$(VENV_DIR)/bin/pyinstaller whisper-transcriber.spec --clean

build-all: clean ## Build for all platforms (requires Docker)
	@echo "$(BLUE)Building for all platforms...$(NC)"
	make build-windows
	make build-linux
	make build-macos

build-windows: ## Build Windows executable
	@echo "$(BLUE)Building Windows executable...$(NC)"
	docker run --rm -v $(PWD):/workspace \
		python:3.11-windowsservercore \
		powershell -Command "cd /workspace; pip install pyinstaller; pip install -r requirements.txt; pyinstaller whisper-transcriber.spec --clean"

build-linux: ## Build Linux executable
	@echo "$(BLUE)Building Linux executable...$(NC)"
	docker run --rm -v $(PWD):/workspace \
		python:3.11-slim \
		bash -c "cd /workspace && apt-get update && apt-get install -y build-essential && pip install pyinstaller && pip install -r requirements.txt && pyinstaller whisper-transcriber.spec --clean"

build-macos: ## Build macOS executable (requires macOS)
ifeq ($(PLATFORM),macos)
	@echo "$(BLUE)Building macOS executable...$(NC)"
	$(VENV_DIR)/bin/pip install pyinstaller
	$(VENV_DIR)/bin/pyinstaller whisper-transcriber.spec --clean
	# Create DMG
	create-dmg --volname "Whisper Transcriber" \
		--window-pos 200 120 \
		--window-size 800 400 \
		--icon-size 100 \
		--icon "Whisper Transcriber.app" 200 190 \
		--hide-extension "Whisper Transcriber.app" \
		--app-drop-link 600 185 \
		"dist/Whisper-Transcriber-$(VERSION).dmg" \
		"dist/"
else
	@echo "$(RED)macOS build requires macOS platform$(NC)"
	@exit 1
endif

# Package targets
package: build ## Create distribution package
	@echo "$(BLUE)Creating distribution package...$(NC)"
	mkdir -p dist/$(APP_NAME)-$(VERSION)-$(PLATFORM)
	cp -r dist/$(APP_NAME)/* dist/$(APP_NAME)-$(VERSION)-$(PLATFORM)/
	cp README.md LICENSE dist/$(APP_NAME)-$(VERSION)-$(PLATFORM)/
	cd dist && tar -czf $(APP_NAME)-$(VERSION)-$(PLATFORM).tar.gz $(APP_NAME)-$(VERSION)-$(PLATFORM)/

# Development helpers
run: ## Run the application in development mode
	@echo "$(BLUE)Running application...$(NC)"
	$(VENV_DIR)/bin/python main.py --gui

run-web: ## Run web interface
	@echo "$(BLUE)Running web interface...$(NC)"
	$(VENV_DIR)/bin/python main.py --web --web-port 3000

run-console: ## Run console interface
	@echo "$(BLUE)Running console interface...$(NC)"
	$(VENV_DIR)/bin/python main.py

# Docker targets
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(APP_NAME):$(VERSION) .
	docker tag $(APP_NAME):$(VERSION) $(APP_NAME):latest

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -it --rm -p 3000:3000 $(APP_NAME):latest

# CI/CD helpers
ci-setup: ## Setup CI environment
	@echo "$(BLUE)Setting up CI environment...$(NC)"
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -r requirements-dev.txt

release-check: ## Check if ready for release
	@echo "$(BLUE)Checking release readiness...$(NC)"
	@echo "Current version: $(VERSION)"
	make lint
	make test
	@echo "$(GREEN)Release check passed!$(NC)"

# Maintenance
update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(VENV_DIR)/bin/pip-compile requirements.in
	$(VENV_DIR)/bin/pip-compile requirements-dev.in
	$(VENV_DIR)/bin/pip install -r requirements.txt
	$(VENV_DIR)/bin/pip install -r requirements-dev.txt

# Information
info: ## Show project information
	@echo "$(BLUE)Project Information$(NC)"
	@echo "==================="
	@echo "App Name: $(APP_NAME)"
	@echo "Version: $(VERSION)"
	@echo "Platform: $(PLATFORM)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Virtual Env: $(VENV_DIR)"
