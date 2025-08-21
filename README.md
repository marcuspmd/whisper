# Whisper local (faster-whisper)

Script simples para capturar áudio do microfone, transcrever com `faster-whisper` e traduzir palavras para português usando `googletrans`.

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