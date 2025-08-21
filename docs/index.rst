Whisper Transcriber Documentation
==================================

Um aplicativo profissional de transcrição de áudio em tempo real usando OpenAI Whisper com interface gráfica moderna, recursos avançados de teleprompter e suporte multi-plataforma.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api

Funcionalidades
===============

Transcrição Avançada
--------------------

* **Transcrição em tempo real** com OpenAI Whisper
* **Detecção de atividade de voz (VAD)** para economia de recursos
* **Múltiplos modelos Whisper** (tiny, base, small, medium, large)
* **Suporte a múltiplos idiomas** com detecção automática
* **Tradução automática** para vários idiomas

Teleprompter Profissional
-------------------------

* **Interface transparente** para uso em streaming/gravação
* **Controle de velocidade** de rolagem automática
* **Texto sempre visível** com fundo personalizável
* **Posicionamento flexível** na tela

Interface Moderna
-----------------

* **Design responsivo** com CustomTkinter
* **Tema escuro/claro** configurável
* **Controles intuitivos** e acessíveis

Recursos Técnicos
-----------------

* **Múltiplos dispositivos de áudio** suportados
* **Configurações persistentes** com gerenciamento avançado
* **Exportação** de transcrições em múltiplos formatos
* **Logs detalhados** para debugging
* **Performance otimizada** com cache inteligente

Instalação Rápida
=================

Usando Make (Recomendado)
-------------------------

.. code-block:: bash

   # Clone o repositório
   git clone https://github.com/marcuspmd/whisper-transcriber.git
   cd whisper-transcriber

   # Instale dependências
   make install

   # Execute o aplicativo
   make run

Instalação Manual
-----------------

macOS
~~~~~

.. code-block:: bash

   # Instale dependências do sistema
   brew install portaudio ffmpeg

   # Crie ambiente virtual
   python3 -m venv .venv
   source .venv/bin/activate

   # Instale dependências Python
   pip install -r requirements.txt

Linux (Ubuntu/Debian)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Instale dependências do sistema
   sudo apt-get update
   sudo apt-get install portaudio19-dev ffmpeg python3-dev

   # Crie ambiente virtual
   python3 -m venv .venv
   source .venv/bin/activate

   # Instale dependências Python
   pip install -r requirements.txt

Windows
~~~~~~~

.. code-block:: bash

   # Crie ambiente virtual
   python -m venv .venv
   .venv\Scripts\activate

   # Instale dependências Python
   pip install -r requirements.txt

Como Usar
=========

Interface Gráfica (GUI)
-----------------------

.. code-block:: bash

   python main.py --gui
   # ou
   make run

Linha de Comando
----------------

.. code-block:: bash

   # Transcrição básica
   python main.py --model base --language pt

   # Com tradução
   python main.py --translate-to pt --model small

   # Modo teleprompter
   python main.py --teleprompter --transparent

   # Listar dispositivos de áudio
   python main.py --list-devices

API Reference
=============

.. automodule:: src.app
   :members:

.. automodule:: src.audio.device_manager
   :members:

.. automodule:: src.transcription.whisper_engine
   :members:

.. automodule:: src.translation.engines
   :members:

.. automodule:: src.ui.desktop
   :members:

.. automodule:: src.config.settings
   :members:

Índices e tabelas
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`