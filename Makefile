.PHONY: help clean build build-macos build-all

# Variables
PYTHON := python3
VENV_DIR := .venv
APP_NAME := whisper-transcriber

# Colors
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m

help: ## Show help
	@echo "Available targets:"
	@echo "  build-macos    - Build for macOS"
	@echo "  build-all      - Build for supported platforms"
	@echo "  clean          - Clean build artifacts"

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf __pycache__/ */__pycache__/ */*/__pycache__/

build: clean ## Build for current platform
	@echo "$(BLUE)Building executable...$(NC)"
	$(VENV_DIR)/bin/pip install pyinstaller
	$(VENV_DIR)/bin/pyinstaller whisper-transcriber.spec --clean

build-macos: clean ## Build macOS executable
	@echo "$(BLUE)Building macOS executable...$(NC)"
	$(VENV_DIR)/bin/pip install pyinstaller
	$(VENV_DIR)/bin/pyinstaller whisper-transcriber.spec --clean
	@echo "$(GREEN)App bundle created at dist/Whisper Transcriber.app$(NC)"

build-all: clean ## Build for all supported platforms
	@echo "$(BLUE)Building for supported platforms...$(NC)"
	make build-macos
	@echo "$(GREEN)Build completed!$(NC)"
