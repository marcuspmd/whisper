Guia de Início Rápido
====================

Este guia mostra como começar a usar o Whisper Transcriber rapidamente.

Primeiro Uso
------------

1. **Lista dispositivos de áudio disponíveis:**

.. code-block:: bash

   python main.py --list-devices

Exemplo de saída:

.. code-block:: text

   === Dispositivos de Áudio Disponíveis ===
   ID  | Entradas | Saídas | Nome
   --------------------------------------------------
    0  |    --    |    2   | Alto-falantes (MacBook Pro)
    1  |     1    |   --   | Microfone (MacBook Pro)
    2  |     2    |    2   | BlackHole 2ch

2. **Execute com interface gráfica:**

.. code-block:: bash

   python main.py --gui
   # ou
   make run

3. **Execute em modo console simples:**

.. code-block:: bash

   python main.py --simple

Modos de Operação
-----------------

Interface Gráfica (GUI)
~~~~~~~~~~~~~~~~~~~~~~~

O modo mais completo e recomendado:

.. code-block:: bash

   python main.py --gui

Recursos:
- Interface moderna com CustomTkinter
- Controles visuais para todas as configurações
- Visualização em tempo real da transcrição
- Gerenciamento de dispositivos de áudio
- Controle de volume e VAD

Console Interativo
~~~~~~~~~~~~~~~~~~

Interface em terminal com controles básicos:

.. code-block:: bash

   python main.py

Recursos:
- Interface textual rica
- Controles por teclado
- Adequado para uso em servidores

Console Simples
~~~~~~~~~~~~~~~

Saída direta no terminal:

.. code-block:: bash

   python main.py --simple

Recursos:
- Saída mínima
- Ideal para scripts e automação
- Menor uso de recursos

Modo Teleprompter
~~~~~~~~~~~~~~~~~

Janela transparente para streaming:

.. code-block:: bash

   python main.py --teleprompter

Recursos:
- Janela sempre no topo
- Transparência configurável
- Ideal para streaming e gravação

Configurações Básicas
---------------------

Seleção de Dispositivo de Áudio
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Por ID:

.. code-block:: bash

   python main.py --device-id 1

Por nome (substring):

.. code-block:: bash

   python main.py --device-name "BlackHole"

Modelo Whisper
~~~~~~~~~~~~~~

Escolha o modelo baseado na qualidade vs velocidade:

.. code-block:: bash

   # Mais rápido, menor qualidade
   python main.py --model tiny

   # Balanceado (padrão)
   python main.py --model base

   # Melhor qualidade, mais lento
   python main.py --model large

Idioma
~~~~~~

Auto-detecção (padrão):

.. code-block:: bash

   python main.py

Forçar idioma específico:

.. code-block:: bash

   python main.py --language pt    # Português
   python main.py --language en    # Inglês
   python main.py --language es    # Espanhol

Tradução
~~~~~~~~

Desabilitar tradução:

.. code-block:: bash

   python main.py --no-translate

Tradução local (offline):

.. code-block:: bash

   python main.py --translate-mode local

Google Translate (online):

.. code-block:: bash

   python main.py --translate-mode google

Idioma de destino:

.. code-block:: bash

   python main.py --target-language en

Detecção de Atividade de Voz (VAD)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Habilitar VAD para economia de recursos:

.. code-block:: bash

   python main.py --use-vad

Ajustar sensibilidade (0-3):

.. code-block:: bash

   python main.py --use-vad --vad-aggressiveness 3

Configurações Avançadas
-----------------------

Intervalo de Processamento
~~~~~~~~~~~~~~~~~~~~~~~~~

Ajustar intervalo de captura (em segundos):

.. code-block:: bash

   # Mais responsivo, maior uso de CPU
   python main.py --chunk-seconds 1

   # Mais eficiente, menos responsivo
   python main.py --chunk-seconds 5

Taxa de Amostragem
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py --sample-rate 16000  # Padrão
   python main.py --sample-rate 44100  # Maior qualidade

Dispositivo de Processamento
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py --device cpu     # CPU (padrão)
   python main.py --device cuda    # GPU NVIDIA

Salvar Configurações
~~~~~~~~~~~~~~~~~~~

Salvar configurações atuais como padrão:

.. code-block:: bash

   python main.py --save-config --model large --language pt

Resetar para configurações de fábrica:

.. code-block:: bash

   python main.py --reset-config

Exemplos Práticos
-----------------

Transcrição Básica em Português
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py --language pt --model base

Streaming com Tradução
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py --teleprompter --translate-mode local --target-language en

Máxima Qualidade
~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py --model large --chunk-seconds 5 --device cuda

Economia de Recursos
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python main.py --model tiny --use-vad --simple

Gravação de Áudio do Sistema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # No macOS com BlackHole
   python main.py --device-name "BlackHole" --model base

Logs e Debugging
----------------

Habilitar logs detalhados:

.. code-block:: bash

   python main.py --log-level DEBUG

Verificar arquivo de log:

.. code-block:: bash

   tail -f logs/app.log

Desabilitar cores nos logs:

.. code-block:: bash

   python main.py --no-color

Próximos Passos
--------------

- Explore a :doc:`api` para integração customizada
- Configure atalhos de teclado personalizados
- Experimente diferentes combinações de modelos e configurações
- Considere usar GPU para modelos maiores