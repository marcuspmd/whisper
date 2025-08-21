import os
import warnings
# Suprimir aviso conhecido do pkg_resources (emitido por algumas versões de wheels como webrtcvad)
# Isto é um workaround temporário — também adicionamos `setuptools<81` em requirements.txt.
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
    )
    # imports que podem acionar o aviso devem ser feitas após esta supressão
    pass
import tempfile
import argparse
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
from googletrans import Translator
import threading
import queue
import multiprocessing as mp
import time
from collections import deque
import sys
from itertools import islice

try:
    from transformers import MarianMTModel, MarianTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


# Configurações padrão de áudio
CHANNELS = 1
RATE = 16000
CHUNK_SECONDS = 3  # chunks maiores para melhor precisão
BUFFER_SECONDS = 15  # mantém 15 segundos de contexto
OVERLAP_SECONDS = 1  # sobreposição para manter contexto


def list_audio_devices():
    """Lista todos os dispositivos de áudio disponíveis."""
    try:
        devices = sd.query_devices()
    except Exception:
        try:
            devices = sd.devices
        except Exception:
            print("Erro ao consultar dispositivos de áudio.")
            return

    print("\n=== Dispositivos de Áudio Disponíveis ===")
    print("ID  | Entradas | Saídas | Nome")
    print("-" * 50)

    for idx, dev in enumerate(devices):
        name = dev.get('name') if isinstance(dev, dict) else getattr(dev, 'name', '')
        max_in = dev.get('max_input_channels', 0) if isinstance(dev, dict) else getattr(dev, 'max_input_channels', 0)
        max_out = dev.get('max_output_channels', 0) if isinstance(dev, dict) else getattr(dev, 'max_output_channels', 0)

        in_str = f"{max_in:2d}" if max_in > 0 else "--"
        out_str = f"{max_out:2d}" if max_out > 0 else "--"

        print(f"{idx:2d}  |    {in_str}    |   {out_str}   | {name}")
    print()


def transcribe_process_main(q: mp.Queue, control_pipe, model_name_local, device_local, translate_mode_local, no_translate_local, use_vad_local, vad_aggressiveness_local):
    # Carrega modelo e tradutor neste processo
    try:
        local_model = WhisperModel(model_name_local, device=device_local, compute_type='int8')
    except Exception as e:
        print(f"Erro ao carregar modelo no processo de transcrição: {e}")
        return

    local_local_tokenizer = None
    local_local_model = None
    local_translator = None
    if not no_translate_local:
        if translate_mode_local == 'local' and TRANSFORMERS_AVAILABLE:
            try:
                local_local_tokenizer = MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-en-pt')
                local_local_model = MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-en-pt')
            except Exception:
                local_translator = Translator()
        else:
            local_translator = Translator()

    vad_obj = None
    if use_vad_local:
        try:
            import webrtcvad
            vad_obj = webrtcvad.Vad(vad_aggressiveness_local)
        except Exception:
            vad_obj = None

    recent_local = deque(maxlen=5)

    while True:
        if control_pipe.poll():
            cmd = control_pipe.recv()
            if cmd == 'STOP':
                break

        try:
            item = q.get(timeout=0.5)
        except Exception:
            continue

        try:
            audio_bytes, sample_rate, lang = item
            arr = np.frombuffer(audio_bytes, dtype=np.int16)

            # VAD check: use webrtcvad if disponível, senão fallback RMS
            accept = True
            if vad_obj is not None:
                frame_ms = 30
                frame_len = int(sample_rate * frame_ms / 1000)
                if len(arr) < frame_len:
                    accept = False
                else:
                    last_frame = arr[-frame_len:]
                    try:
                        is_speech = vad_obj.is_speech(last_frame.tobytes(), sample_rate)
                        accept = is_speech
                    except Exception:
                        accept = True
            else:
                rms = np.sqrt(np.mean(arr.astype(float)**2))
                accept = rms > 25

            if not accept:
                continue

            # escreve temp e transcreve
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    tmp_path = tmp.name
                    sf.write(tmp.name, arr, sample_rate, subtype='PCM_16')

                transcribe_params = {"beam_size":1, "best_of":1, "temperature":0.0, "condition_on_previous_text":False}
                if lang:
                    transcribe_params['language'] = lang

                segments, _ = local_model.transcribe(tmp_path, **transcribe_params)
                for segment in segments:
                    text = getattr(segment, 'text', '').strip()
                    if not text:
                        continue
                    if text.lower() in [r.lower() for r in recent_local]:
                        continue
                    recent_local.append(text)
                    translated = None
                    if not no_translate_local:
                        try:
                            if local_local_model and local_local_tokenizer:
                                inputs = local_local_tokenizer(text, return_tensors='pt', padding=True)
                                tokens = local_local_model.generate(**inputs)
                                translated = local_local_tokenizer.decode(tokens[0], skip_special_tokens=True)
                            elif local_translator:
                                translated = local_translator.translate(text, dest='pt').text
                        except Exception:
                            translated = None

                    ts = time.strftime('%H:%M:%S')
                    if translated:
                        print(f"\n[{ts}] {text} ➜ {translated}")
                    else:
                        print(f"\n[{ts}] {text}")

            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

        except Exception as e:
            print(f"Erro no processo de transcrição: {e}")
            continue


def find_input_device_by_name(name_substring: str):
    """Procura o primeiro dispositivo de entrada cujo nome contenha name_substring (case-insensitive).
    Retorna o índice do dispositivo ou None se não encontrado."""
    try:
        devices = sd.query_devices()
    except Exception:
        try:
            devices = sd.devices
        except Exception:
            return None

    candidates = []
    for idx, dev in enumerate(devices):
        # cada dev deve ser um dict com 'name' e 'max_input_channels'
        name = dev.get('name') if isinstance(dev, dict) else getattr(dev, 'name', None)
        max_in = dev.get('max_input_channels') if isinstance(dev, dict) else getattr(dev, 'max_input_channels', 0)
        if name and (name_substring.lower() in name.lower()) and max_in and max_in > 0:
            candidates.append((idx, name))

    if candidates:
        return candidates[0][0]
    return None


def find_device_by_id(device_id: int):
    """Verifica se o dispositivo com ID existe e retorna suas informações."""
    try:
        devices = sd.query_devices()
        if 0 <= device_id < len(devices):
            dev = devices[device_id]
            name = dev.get('name') if isinstance(dev, dict) else getattr(dev, 'name', '')
            max_in = dev.get('max_input_channels', 0) if isinstance(dev, dict) else getattr(dev, 'max_input_channels', 0)
            return (device_id, name, max_in)
    except Exception:
        pass
    return None


def main(model_name="base", device="cpu", input_device_name: str = None, input_device_id: int = None, rate: int = RATE, chunk_seconds: int = CHUNK_SECONDS, translate_mode="google", no_translate=False, list_devices=False, language=None, tail_check_ms: int = 120, silence_threshold: float = 50.0, lookahead_seconds: float = None, use_vad: bool = False, vad_aggressiveness: int = 2):
    # NOTA: o processo principal apenas captura e empacota; o processo de transcrição carrega o modelo.
    # Inicializa variáveis locais (modelo será carregado no processo de transcrição)
    translator = None
    local_model = None
    local_tokenizer = None

    if not no_translate:
        if translate_mode == "local" and TRANSFORMERS_AVAILABLE:
            print("Carregando modelo de tradução local...")
            model_name_trans = "Helsinki-NLP/opus-mt-en-pt"
            try:
                local_tokenizer = MarianTokenizer.from_pretrained(model_name_trans)
                local_model = MarianMTModel.from_pretrained(model_name_trans)
                print("Modelo local carregado com sucesso!")
            except Exception as e:
                print(f"Erro ao carregar modelo local: {e}")
                print("Usando Google Translate como fallback...")
                translator = Translator()
        else:
            translator = Translator()

    # cache simples de traduções para evitar chamadas repetidas e acelerar
    translation_cache = {}

    # Lista dispositivos se solicitado
    if list_devices:
        list_audio_devices()
        return

    # Seleciona dispositivo de entrada se solicitado
    device_index = None
    device_info = None

    if input_device_id is not None:
        device_info = find_device_by_id(input_device_id)
        if device_info is None:
            print(f"Dispositivo #{input_device_id} não encontrado. Usando dispositivo padrão.")
        elif device_info[2] == 0:  # max_input_channels
            print(f"Dispositivo #{input_device_id} '{device_info[1]}' não suporta entrada de áudio. Usando dispositivo padrão.")
        else:
            device_index = device_info[0]
            print(f"Usando dispositivo de entrada #{device_index}: {device_info[1]}\n")
    elif input_device_name:
        device_index = find_input_device_by_name(input_device_name)
        if device_index is None:
            print(f"Nenhum dispositivo contendo '{input_device_name}' foi encontrado. Usando dispositivo padrão.")
        else:
            print(f"Usando dispositivo de entrada #{device_index} para '{input_device_name}'.\n")

    # Configura dispositivo se encontrado
    if device_index is not None:
        try:
            sd.default.device = (device_index, sd.default.device[1] if isinstance(sd.default.device, tuple) else None)
        except Exception:
            # sd.default.device pode aceitar apenas um índice dependendo da versão
            sd.default.device = device_index

    # Verifica se há dispositivos de entrada disponíveis
    try:
        inputs = [d for d in sd.query_devices() if (d.get('max_input_channels', 0) if isinstance(d, dict) else getattr(d, 'max_input_channels', 0)) > 0]
        if not inputs:
            print("Nenhum dispositivo de entrada de áudio encontrado. Verifique microfone/permissões.")
            return
    except Exception:
        print("Erro ao consultar dispositivos de áudio. Verifique permissões.")
        return

    print("🎙️ Captura contínua de áudio... (Ctrl+C para parar)\n")

    # Buffer circular para captura contínua sem perdas
    audio_buffer = deque(maxlen=int(BUFFER_SECONDS * rate))
    buffer_lock = threading.Lock()
    stop_flag = threading.Event()

    # Variáveis de runtime para o pipeline multiprocessing
    transcribe_queue = None
    parent_conn = None
    trans_proc = None
    packer = None

    # Cache para evitar repetições
    recent_texts = deque(maxlen=5)  # últimos 5 textos

    def print_status(msg, replace_last=False):
        """Imprime status na mesma linha"""
        if replace_last:
            print(f"\r\033[K{msg}", end="", flush=True)
        else:
            print(f"\n{msg}")

    def audio_callback(indata, frames, time_info, status):
        """Callback chamado pelo sounddevice para capturar áudio continuamente"""
        try:
            # Adiciona ao buffer (thread-safe)
            with buffer_lock:
                audio_buffer.extend(indata[:, 0].astype(np.int16))  # primeiro canal apenas
        except Exception as e:
            print(f"\n❌ Erro no callback: {e}")

    def packer_thread():
        """Thread que empacota chunks e enfileira para o processo de transcrição."""
        last_processed_time = 0
        while not stop_flag.is_set():
            try:
                if stop_flag.wait(chunk_seconds):
                    break

                current_time = time.time()
                if current_time - last_processed_time < chunk_seconds:
                    continue

                with buffer_lock:
                    buffer_size = len(audio_buffer)
                    if buffer_size == 0:
                        print_status("🔇 Aguardando áudio...", replace_last=True)
                        continue

                    # Status do buffer
                    buffer_seconds = buffer_size / rate
                    print_status(f"📡 Buffer: {buffer_seconds:.1f}s", replace_last=True)

                    required_samples = int(chunk_seconds * rate)
                    if buffer_size < required_samples:
                        continue

                    try:
                        effective_lookahead = lookahead_seconds if (lookahead_seconds is not None) else max(OVERLAP_SECONDS, 1.0)
                        lookahead_max_samples = int(max(effective_lookahead, 0.0) * rate)

                        max_needed = min(buffer_size, required_samples + lookahead_max_samples)
                        start_copy_idx = buffer_size - max_needed
                        tail_iter = islice(audio_buffer, start_copy_idx, None)
                        audio_tail = np.fromiter(tail_iter, dtype=np.int16, count=max_needed)

                        if len(audio_tail) >= required_samples:
                            audio_segment = audio_tail[-required_samples:]
                        else:
                            audio_segment = audio_tail.copy()

                        tail_check_seconds = max(tail_check_ms / 1000.0, 0.02)
                        tail_check_samples = max(int(tail_check_seconds * rate), 1)

                        def is_tail_silent_array(arr):
                            if len(arr) < tail_check_samples:
                                return False
                            tail = arr[-tail_check_samples:]
                            rms = np.sqrt(np.mean(tail.astype(float)**2))
                            return rms < silence_threshold

                        if not is_tail_silent_array(audio_segment):
                            extra_available = len(audio_tail) - len(audio_segment)
                            extra_taken = 0
                            step = int(0.2 * rate)
                            while extra_taken < extra_available:
                                extra_taken = min(extra_available, extra_taken + step)
                                new_len = len(audio_segment) + extra_taken
                                audio_segment = audio_tail[-new_len:]
                                if is_tail_silent_array(audio_segment):
                                    break

                        last_processed_time = current_time
                    except Exception as e:
                        print(f"\n❌ Erro ao copiar buffer: {e}")
                        continue

                # Verifica se há áudio suficiente
                if len(audio_segment) < rate * 0.5:
                    continue

                # Detecção de atividade de voz por RMS antes de enfileirar
                volume_rms = np.sqrt(np.mean(audio_segment.astype(float)**2))
                if volume_rms < 25:
                    print_status(f"🔇 Silêncio (RMS: {volume_rms:.0f})", replace_last=True)
                    continue

                # Normalização leve
                max_val = np.max(np.abs(audio_segment))
                if max_val > 0:
                    audio_segment = (audio_segment / max_val * 32767 * 0.85).astype(np.int16)

                # Empacota e envia para a fila de transcrição (sem bloquear a captura)
                try:
                    if not transcribe_queue.full():
                        transcribe_queue.put_nowait((audio_segment.tobytes(), rate, language))
                except Exception:
                    pass

            except Exception as e:
                print(f"Erro no packer_thread: {e}")
                time.sleep(0.5)

    # transcribe_process_main foi movida para o nível do módulo (ver topo do arquivo)

    try:
        # Inicia processo de transcrição
        transcribe_queue = mp.Queue(maxsize=4)
        parent_conn, child_conn = mp.Pipe()
        trans_proc = mp.Process(target=transcribe_process_main, args=(transcribe_queue, child_conn, model_name, device, translate_mode, no_translate, use_vad, vad_aggressiveness), daemon=True)
        trans_proc.start()

        # Inicia packer thread
        packer = threading.Thread(target=packer_thread, daemon=True)
        packer.start()

        print(f"\n✅ Captura iniciada (dispositivo #{device_index if device_index else 'padrão'})")
        print("🎙️  Fale que será transcrito automaticamente...")
        print("\n" + "="*50)

        # Stream contínuo de áudio com recovery
        with sd.InputStream(
            callback=audio_callback,
            channels=CHANNELS,
            samplerate=rate,
            dtype='int16',
            device=device_index,
            blocksize=int(0.2 * rate),  # 200ms blocks (mais estável)
            latency='low'
        ):
            # Mantém programa vivo com recovery
            while not stop_flag.is_set():
                if stop_flag.wait(5):  # verifica stop_flag a cada 5s
                    break

                if not packer.is_alive():
                    print("\n🔄 Reiniciando packer...")
                    packer = threading.Thread(target=packer_thread, daemon=True)
                    packer.start()

    except KeyboardInterrupt:
        print("\n\n🛑 Parando captura...")
        stop_flag.set()

        # tenta encerrar packer e processo de transcrição de forma limpa
        try:
            if packer is not None and packer.is_alive():
                packer.join(timeout=1)
        except Exception:
            pass

        # envia sentinela na queue para sinalizar término
        try:
            if transcribe_queue is not None:
                try:
                    transcribe_queue.put_nowait(None)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            if parent_conn is not None:
                parent_conn.send('STOP')
        except Exception:
            pass

        try:
            if trans_proc is not None and trans_proc.is_alive():
                trans_proc.join(timeout=2)
        except Exception:
            pass

        print("✅ Finalizado!")
        os._exit(0)  # saída forçada

    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        stop_flag.set()
        os._exit(1)

    finally:
        stop_flag.set()
        # cleanup: envia sentinela se a queue existir
        try:
            if transcribe_queue is not None:
                try:
                    transcribe_queue.put_nowait(None)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            if parent_conn is not None:
                parent_conn.send('STOP')
        except Exception:
            pass

        try:
            if trans_proc is not None and trans_proc.is_alive():
                trans_proc.join(timeout=2)
        except Exception:
            pass

        os._exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Grava, transcreve e traduz áudio (faster-whisper + googletrans)')
    parser.add_argument('--model', default='base', help='Nome do modelo Whisper (ex: base, small, medium)')
    parser.add_argument('--device', default='cpu', help='Dispositivo para o modelo (cpu/gpu)')
    parser.add_argument('--input-device-name', default=None, help='Substring do nome do dispositivo de entrada para usar (ex: BlackHole)')
    parser.add_argument('--input-device-id', type=int, default=None, help='ID do dispositivo de entrada (use --list-devices para ver os IDs)')
    parser.add_argument('--list-devices', action='store_true', help='Lista todos os dispositivos de áudio disponíveis e sai')
    parser.add_argument('--rate', type=int, default=RATE, help='Sample rate de gravação')
    parser.add_argument('--chunk-seconds', type=int, default=CHUNK_SECONDS, help='Intervalo de processamento (segundos)')
    parser.add_argument('--language', default=None, help='Idioma do áudio (ex: en, pt, es) - auto-detecta se não especificado')
    parser.add_argument('--translate-mode', default='local', choices=['local', 'google'], help='Modo de tradução (google ou local)')
    parser.add_argument('--no-translate', action='store_true', help='Desabilita tradução (apenas transcrição)')
    parser.add_argument('--tail-check-ms', type=int, default=120, help='Janela (ms) para checar silêncio no final do chunk (p.ex. 120)')
    parser.add_argument('--silence-threshold', type=float, default=50.0, help='Threshold RMS para considerar silêncio (valor mais baixo = mais sensível)')
    parser.add_argument('--lookahead-seconds', type=float, default=None, help='Máximo de segundos para estender o chunk procurando silêncio (p.ex. 1.0). Se omitido usa OVERLAP_SECONDS ou 1s.')
    parser.add_argument('--use-vad', action='store_true', help='Usar webrtcvad para detectar final de fala (se instalado).')
    parser.add_argument('--vad-aggressiveness', type=int, default=2, choices=[0,1,2,3], help='Nível de agressividade do webrtcvad (0-3).')
    args = parser.parse_args()

    main(
        model_name=args.model,
        device=args.device,
        input_device_name=args.input_device_name,
        input_device_id=args.input_device_id,
        rate=args.rate,
        chunk_seconds=args.chunk_seconds,
        language=args.language,
        translate_mode=args.translate_mode,
        no_translate=args.no_translate,
        list_devices=args.list_devices,
        tail_check_ms=args.tail_check_ms,
        silence_threshold=args.silence_threshold,
        lookahead_seconds=args.lookahead_seconds,
    use_vad=args.use_vad,
    vad_aggressiveness=args.vad_aggressiveness,
    )
