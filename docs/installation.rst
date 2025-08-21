Instalação
==========

Requisitos do Sistema
---------------------

Mínimos
~~~~~~~

* **Python**: 3.8 ou superior
* **RAM**: 4GB (modelo tiny/base) / 8GB (modelo large)
* **Armazenamento**: 2GB livres
* **Processador**: Dual-core 2.0GHz
* **Audio**: Dispositivo de entrada (microfone)

Recomendados
~~~~~~~~~~~~

* **Python**: 3.11 ou superior
* **RAM**: 16GB ou superior
* **GPU**: NVIDIA com 6GB+ VRAM (para aceleração CUDA)
* **Armazenamento**: SSD com 10GB+ livres
* **Processador**: Quad-core 3.0GHz ou superior

Sistemas Operacionais Suportados
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **macOS**: 10.15 (Catalina) ou superior
* **Windows**: 10 ou superior (64-bit)
* **Linux**: Ubuntu 18.04+, Debian 10+, CentOS 8+

Instalação por Plataforma
-------------------------

macOS
~~~~~

1. Instale o Homebrew (se ainda não tiver):
   https://brew.sh/

2. Instale dependências nativas:

.. code-block:: bash

   brew install portaudio ffmpeg

3. Clone o repositório:

.. code-block:: bash

   git clone https://github.com/marcuspmd/whisper-transcriber.git
   cd whisper-transcriber

4. Crie e ative um virtualenv:

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate

5. Instale dependências Python:

.. code-block:: bash

   pip install -r requirements.txt

Linux (Ubuntu/Debian)
~~~~~~~~~~~~~~~~~~~~~~

1. Instale dependências do sistema:

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install portaudio19-dev ffmpeg python3-dev python3-venv

2. Clone o repositório:

.. code-block:: bash

   git clone https://github.com/marcuspmd/whisper-transcriber.git
   cd whisper-transcriber

3. Crie e ative um virtualenv:

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate

4. Instale dependências Python:

.. code-block:: bash

   pip install -r requirements.txt

Windows
~~~~~~~

1. Baixe e instale Python 3.8+ do site oficial:
   https://www.python.org/downloads/

2. Clone o repositório:

.. code-block:: bash

   git clone https://github.com/marcuspmd/whisper-transcriber.git
   cd whisper-transcriber

3. Crie e ative um virtualenv:

.. code-block:: bash

   python -m venv .venv
   .venv\Scripts\activate

4. Instale dependências Python:

.. code-block:: bash

   pip install -r requirements.txt

Usando Make (Recomendado)
-------------------------

Se você tem `make` instalado, pode usar os comandos simplificados:

.. code-block:: bash

   # Instale dependências de produção
   make install

   # Instale dependências de desenvolvimento
   make install-dev

   # Execute o aplicativo
   make run

Verificação da Instalação
-------------------------

Para verificar se tudo foi instalado corretamente:

.. code-block:: bash

   python main.py --list-devices

Este comando deve listar todos os dispositivos de áudio disponíveis.

Problemas Comuns
----------------

Erro de microfone no macOS
~~~~~~~~~~~~~~~~~~~~~~~~~~

Se você receber erros relacionados ao microfone:

1. Verifique permissões nas Preferências do Sistema > Segurança e Privacidade > Microfone
2. Reinstale PyAudio:

.. code-block:: bash

   brew install portaudio
   pip uninstall pyaudio
   pip install pyaudio

Erro CUDA no Linux
~~~~~~~~~~~~~~~~~~~

Para usar aceleração GPU:

.. code-block:: bash

   # Instale drivers NVIDIA e CUDA Toolkit
   # Verifique versão: nvidia-smi
   # Reinstale PyTorch com suporte CUDA:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

Erro de dependência no Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Se você tiver problemas com compilação de dependências:

.. code-block:: bash

   # Instale Microsoft C++ Build Tools
   # Ou use conda:
   conda install pyaudio
   conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia