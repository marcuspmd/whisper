# 🎙️ Whisper Transcriber

[![Tests](https://github.com/yourusername/whisper-transcriber/actions/workflows/tests.yml/badge.svg)](https://github.com/yourusername/whisper-transcriber/actions/workflows/tests.yml)
[![Build and Release](https://github.com/yourusername/whisper-transcriber/actions/workflows/build-and-release.yml/badge.svg)](https://github.com/yourusername/whisper-transcriber/actions/workflows/build-and-release.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://hub.docker.com/r/yourusername/whisper-transcriber)

Um aplicativo profissional de transcrição de áudio em tempo real usando OpenAI Whisper com interface gráfica moderna, recursos avançados de teleprompter e suporte multi-plataforma.

## ✨ Funcionalidades

### 🎯 Transcrição Avançada
- **Transcrição em tempo real** com OpenAI Whisper
- **Detecção de atividade de voz (VAD)** para economia de recursos
- **Múltiplos modelos Whisper** (tiny, base, small, medium, large)
- **Suporte a múltiplos idiomas** com detecção automática
- **Tradução automática** para vários idiomas

### 📺 Teleprompter Profissional
- **Interface transparente** para uso em streaming/gravação
- **Controle de velocidade** de rolagem automática
- **Texto sempre visível** com fundo personalizável
- **Posicionamento flexível** na tela

### 🎨 Interface Moderna
- **Design responsivo** com CustomTkinter
- **Tema escuro/claro** configurável
- **Controles intuitivos** e acessíveis

### 🔧 Recursos Técnicos
- **Múltiplos dispositivos de áudio** suportados
- **Configurações persistentes** com gerenciamento avançado
- **Exportação** de transcrições em múltiplos formatos
- **Logs detalhados** para debugging
- **Performance otimizada** com cache inteligente

## 🚀 Instalação Rápida

### Usando Make (Recomendado)

```bash
# Clone o repositório
git clone https://github.com/yourusername/whisper-transcriber.git
cd whisper-transcriber

# Instale dependências do sistema e Python
make install

# Execute o aplicativo
make run
```

### Instalação Manual

#### macOS
```bash
# Instale dependências do sistema
brew install portaudio ffmpeg

# Crie ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instale dependências Python
pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian)
```bash
# Instale dependências do sistema
sudo apt-get update
sudo apt-get install portaudio19-dev ffmpeg python3-dev

# Crie ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instale dependências Python
pip install -r requirements.txt
```

#### Windows
```bash
# Crie ambiente virtual
python -m venv .venv
.venv\Scripts\activate

# Instale dependências Python
pip install -r requirements.txt
```

## 🎮 Como Usar

### Interface Gráfica (GUI)
```bash
python main.py
# ou
make run
```

### Linha de Comando
```bash
# Transcrição básica
python main.py --model base --language pt

# Com tradução
python main.py --translate-to pt --model small

# Modo teleprompter
python main.py --teleprompter --transparent

# Listar dispositivos de áudio
python main.py --list-devices
```

### Docker
```bash
# Build da imagem
docker build -t whisper-transcriber .

# Execute com GUI (X11 forwarding no Linux)
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  --device /dev/snd \
  whisper-transcriber
```

## 🛠️ Desenvolvimento

### Configuração do Ambiente de Desenvolvimento

```bash
# Clone e configure
git clone https://github.com/yourusername/whisper-transcriber.git
cd whisper-transcriber

# Instale dependências de desenvolvimento
make install-dev

# Execute testes
make test

# Verificação de qualidade de código
make lint
make format
make type-check
```

### Comandos Make Disponíveis

```bash
make help              # Mostra todos os comandos disponíveis
make install           # Instala dependências de produção
make install-dev       # Instala dependências de desenvolvimento
make run               # Execute o aplicativo
make test              # Execute todos os testes
make test-unit         # Execute apenas testes unitários
make test-integration  # Execute testes de integração
make lint              # Verificação de código (flake8)
make format            # Formatação de código (black, isort)
make type-check        # Verificação de tipos (mypy)
make build             # Build do executável nativo
make build-all         # Build para todas as plataformas
make docker-build      # Build da imagem Docker
make docker-run        # Execute container Docker
make clean             # Limpe arquivos temporários
make docs              # Gere documentação
```

### Estrutura do Projeto

```
whisper-transcriber/
├── src/                    # Código fonte principal
│   ├── __init__.py
│   ├── app.py             # Aplicação principal
│   ├── audio/             # Módulos de áudio
│   ├── config/            # Gerenciamento de configuração
│   ├── ui/                # Interface do usuário
│   └── utils/             # Utilitários diversos
├── tests/                 # Testes automatizados
├── docs/                  # Documentação
├── scripts/               # Scripts de build e deployment
├── .github/               # GitHub Actions CI/CD
├── Dockerfile             # Configuração Docker
├── Makefile              # Automação de build
├── setup.py              # Configuração de pacote Python
├── requirements.txt       # Dependências de produção
├── requirements-dev.txt   # Dependências de desenvolvimento
└── README.md             # Esta documentação
```

## 📦 Build e Distribuição

### Build de Executáveis Nativos

```bash
# Build para plataforma atual
make build

# Build para todas as plataformas (requer Docker)
make build-all

# Build manual com PyInstaller
pyinstaller whisper-transcriber.spec
```

### Docker

```bash
# Build de imagem local
make docker-build

# Build para múltiplas arquiteturas
docker buildx build --platform linux/amd64,linux/arm64 -t whisper-transcriber .

# Publicar no Docker Hub
docker tag whisper-transcriber yourusername/whisper-transcriber:latest
docker push yourusername/whisper-transcriber:latest
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

```bash
# Configurações de áudio
AUDIO_DEVICE_INDEX=0          # Índice do dispositivo de áudio
AUDIO_SAMPLE_RATE=16000       # Taxa de amostragem
AUDIO_CHUNK_SIZE=1024         # Tamanho do buffer

# Configurações do Whisper
WHISPER_MODEL=base            # Modelo padrão
WHISPER_LANGUAGE=auto         # Idioma de detecção
WHISPER_DEVICE=cpu            # Dispositivo (cpu/cuda)

# Configurações da interface
UI_THEME=dark                 # Tema da interface
UI_SCALING=1.0               # Escala da interface
TELEPROMPTER_SPEED=50        # Velocidade do teleprompter

# Configurações de log
LOG_LEVEL=INFO               # Nível de log
LOG_FILE=logs/app.log        # Arquivo de log
```

### Arquivo de Configuração

Crie um arquivo `config/settings.json`:

```json
{
  "audio": {
    "device_index": 0,
    "sample_rate": 16000,
    "chunk_size": 1024,
    "vad_aggressiveness": 2
  },
  "whisper": {
    "model": "base",
    "language": "auto",
    "device": "cpu",
    "compute_type": "int8"
  },
  "ui": {
    "theme": "dark",
    "scaling": 1.0,
    "always_on_top": false
  },
  "teleprompter": {
    "speed": 50,
    "transparency": 0.8,
    "font_size": 16,
    "auto_scroll": true
  },
  "translation": {
    "enabled": true,
    "target_language": "pt",
    "provider": "google"
  },
  "export": {
    "format": "txt",
    "include_timestamps": true,
    "include_confidence": false
  }
}
```

## 🤝 Contribuindo

### Fluxo de Contribuição

1. **Fork** o repositório
2. **Clone** seu fork
3. **Crie** uma branch para sua feature: `git checkout -b feature/nova-funcionalidade`
4. **Implemente** suas mudanças
5. **Execute** os testes: `make test`
6. **Commit** suas mudanças: `git commit -m "Adiciona nova funcionalidade"`
7. **Push** para sua branch: `git push origin feature/nova-funcionalidade`
8. **Abra** um Pull Request

### Padrões de Código

- **Python**: Seguimos PEP 8 com line length de 127 caracteres
- **Formatação**: Usamos `black` para formatação automática
- **Imports**: Organizados com `isort`
- **Type hints**: Obrigatórios para funções públicas
- **Documentação**: Docstrings em formato Google
- **Testes**: Cobertura mínima de 80%

### Executando Testes

```bash
# Todos os testes
make test

# Testes específicos
pytest tests/test_app.py::TestWhisperApplication::test_app_initialization

# Com cobertura
pytest --cov=src --cov-report=html

# Testes de performance
python -m pytest tests/ -m "not slow"
```

## 🐛 Resolução de Problemas

### Problemas Comuns

**Erro de microfone no macOS:**
```bash
# Verifique permissões nas Preferências do Sistema > Segurança e Privacidade > Microfone
# Reinstale PyAudio:
brew install portaudio
pip uninstall pyaudio
pip install pyaudio
```

**Erro CUDA no Linux:**
```bash
# Instale drivers NVIDIA e CUDA Toolkit
# Verifique versão: nvidia-smi
# Reinstale PyTorch com suporte CUDA:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Erro de dependência no Windows:**
```bash
# Instale Microsoft C++ Build Tools
# Ou use conda:
conda install pyaudio
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
```

### Logs e Debug

```bash
# Execute com logs detalhados
python main.py --log-level DEBUG

# Verifique logs
tail -f logs/app.log

# Debug de dispositivos de áudio
python main.py --list-devices --verbose
```

## 📋 Requisitos do Sistema

### Mínimos
- **Python**: 3.8 ou superior
- **RAM**: 4GB (modelo tiny/base) / 8GB (modelo large)
- **Armazenamento**: 2GB livres
- **Processador**: Dual-core 2.0GHz
- **Audio**: Dispositivo de entrada (microfone)

### Recomendados
- **Python**: 3.11 ou superior
- **RAM**: 16GB ou superior
- **GPU**: NVIDIA com 6GB+ VRAM (para aceleração CUDA)
- **Armazenamento**: SSD com 10GB+ livres
- **Processador**: Quad-core 3.0GHz ou superior

### Sistemas Operacionais Suportados
- **macOS**: 10.15 (Catalina) ou superior
- **Windows**: 10 ou superior (64-bit)
- **Linux**: Ubuntu 18.04+, Debian 10+, CentOS 8+

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- [OpenAI Whisper](https://github.com/openai/whisper) - Modelo de transcrição
- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - Implementação otimizada
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Interface moderna
- [WebRTC VAD](https://github.com/wiseman/py-webrtcvad) - Detecção de atividade de voz

## 🔗 Links Úteis

- [Documentação Completa](https://yourusername.github.io/whisper-transcriber/)
- [Issues e Bug Reports](https://github.com/yourusername/whisper-transcriber/issues)
- [Discussões da Comunidade](https://github.com/yourusername/whisper-transcriber/discussions)
- [Changelog](https://github.com/yourusername/whisper-transcriber/releases)

---

**Feito com ❤️ pela comunidade**

Pré-requisitos macOS:

1. Instale o Homebrew (se ainda não tiver):
   https://brew.sh/

2. Instale dependências nativas:

```bash
brew install portaudio
```

3. Crie e ative um virtualenv (recomendado):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. Instale dependências Python:

```bash
pip install -r requirements.txt
```

Observações:
- `faster-whisper` pode exigir configurações adicionais para CUDA se quiser acelerar na GPU; o exemplo usa CPU por padrão.
- Se tiver problemas com `pyaudio` no macOS, verifique permissões de microfone nas Preferências do Sistema.

Aviso conhecido do webrtcvad:

 - Algumas builds do pacote `webrtcvad` usam `pkg_resources`, que atualmente emite um UserWarning relacionado ao `pkg_resources` estar depreciado.
 - Mitigação aplicada: adicionamos um pin em `requirements.txt` (`setuptools<81`) e uma supressão localizada de warning no `main.py` durante o import; isso evita poluir o log enquanto as dependências não forem atualizadas upstream.
 - Recomendação: quando os mantenedores do `webrtcvad` atualizarem a biblioteca para eliminar o uso de `pkg_resources`, remova a supressão e o pin em `setuptools`.

Como executar:

```bash
python main.py
```

O script gravará trechos curtos (~3s) e imprimirá cada palavra transcrita acompanhada da tradução para português.


 Modos disponíveis:

  1. Mais rápido - Sem tradução:
  python main.py --no-translate

  2. Médio - Tradução local (sem internet):
  python main.py --translate-mode local

  3. Original - Google Translate:
  python main.py --translate-mode google

  Para usar a tradução local, você precisa instalar o transformers:
  pip install transformers torch

  O modelo local será baixado automaticamente na primeira execução e depois fica em cache. Isso deve acelerar
  bastante as traduções!

    Para ver todos os dispositivos disponíveis:
  python main.py --list-devices

  Para usar um dispositivo específico pelo ID:
  python main.py --input-device-id 2

  Para usar pelo nome (como antes):
  python main.py --input-device-name "BlackHole"

  Opções para testar:

  # Para inglês (melhor precisão)
  python main.py --language en --no-translate

  # Modelo melhor (se tiver espaço)
  python main.py --model small --language en

  # Processamento mais longo para máxima qualidade
  python main.py --chunk-seconds 5 --language en