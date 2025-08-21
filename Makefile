.PHONY: help clean build build-macos build-all install install-dev run test test-unit test-integration lint format type-check docker-build docker-run docs

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

help: ## Mostra todos os comandos disponíveis
	@echo "Available targets:"
	@echo "  install          - Instala dependências de produção"
	@echo "  install-dev      - Instala dependências de desenvolvimento"
	@echo "  run              - Execute o aplicativo"
	@echo "  test             - Execute todos os testes"
	@echo "  test-unit        - Execute apenas testes unitários"
	@echo "  test-integration - Execute testes de integração"
	@echo "  lint             - Verificação de código (flake8)"
	@echo "  format           - Formatação de código (black, isort)"
	@echo "  type-check       - Verificação de tipos (mypy)"
	@echo "  build            - Build do executável nativo"
	@echo "  build-all        - Build para todas as plataformas"
	@echo "  docker-build     - Build da imagem Docker"
	@echo "  docker-run       - Execute container Docker"
	@echo "  clean            - Limpe arquivos temporários"
	@echo "  docs             - Gere documentação"

install: ## Instala dependências de produção
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt

install-dev: ## Instala dependências de desenvolvimento
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r requirements.txt
	$(VENV_DIR)/bin/pip install flake8 black isort mypy pytest

run: ## Execute o aplicativo
	@echo "$(BLUE)Running application...$(NC)"
	$(VENV_DIR)/bin/python main.py --gui

test: ## Execute todos os testes
	@echo "$(BLUE)Running all tests...$(NC)"
	$(VENV_DIR)/bin/pytest

test-unit: ## Execute apenas testes unitários
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(VENV_DIR)/bin/pytest tests/unit/

test-integration: ## Execute testes de integração
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(VENV_DIR)/bin/pytest tests/integration/

lint: ## Verificação de código (flake8)
	@echo "$(BLUE)Running code linting...$(NC)"
	$(VENV_DIR)/bin/flake8 src/ tests/

format: ## Formatação de código (black, isort)
	@echo "$(BLUE)Formatting code...$(NC)"
	$(VENV_DIR)/bin/black src/ tests/
	$(VENV_DIR)/bin/isort src/ tests/

type-check: ## Verificação de tipos (mypy)
	@echo "$(BLUE)Running type check...$(NC)"
	$(VENV_DIR)/bin/mypy src/

docker-build: ## Build da imagem Docker
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(APP_NAME) .

docker-run: ## Execute container Docker
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -it --rm $(APP_NAME)


docs: ## Gere documentação
	@echo "$(BLUE)Generating documentation...$(NC)"
	$(VENV_DIR)/bin/pip install sphinx sphinx_rtd_theme
	$(VENV_DIR)/bin/sphinx-build -b html docs/ docs/_build/html/

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf __pycache__/ */__pycache__/ */*/__pycache__/
	rm -rf docs/_build/

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
