"""
Main application orchestrator
"""
import os
import sys
import signal
import threading
import multiprocessing as mp
import time
import numpy as np
from typing import Optional
import logging

# Suprimir warnings do pkg_resources
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
    )

from .audio.device_manager import AudioDeviceManager
from .audio.capture import AudioCapture, VADAudioCapture
from .transcription.whisper_engine import WhisperTranscriber
from .translation.engines import TranslationManager
from .config.settings import get_config_manager
from .ui.simple import create_interactive_console
from .utils.logger import setup_colored_logging

logger = logging.getLogger(__name__)


class WhisperApplication:
    """Aplicação principal de transcrição"""

    def __init__(self, use_simple_ui=False):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        self.use_simple_ui = use_simple_ui

        # Componentes principais
        self.device_manager = AudioDeviceManager()
        self.audio_capture = None
        self.transcriber = None
        self.translation_manager = None
        self.ui = None

        # Estado da aplicação
        self.is_running = False
        self.stop_event = threading.Event()

        # Threads
        self.ui_thread = None
        self.audio_monitor_thread = None
        self.transcription_thread = None

        # Setup inicial
        self._setup_logging()
        self._setup_signal_handlers()

    def _setup_logging(self):
        """Configura sistema de logging"""
        if self.config.ui.colored_logs:
            setup_colored_logging(self.config.ui.log_level)
        else:
            import logging
            logging.basicConfig(level=getattr(logging, self.config.ui.log_level))

    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema"""
        def signal_handler(signum, frame):
            logger.info("Sinal de interrupção recebido, finalizando...")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _setup_audio(self) -> bool:
        """Configura captura de áudio"""
        try:
            # Seleciona dispositivo
            device_index = None
            device_name = "Dispositivo padrão"

            if self.config.audio.device_id is not None:
                device_info = self.device_manager.find_device_by_id(self.config.audio.device_id)
                if device_info and device_info[2] > 0:  # tem entrada
                    device_index = device_info[0]
                    device_name = device_info[1]
                    logger.info(f"Usando dispositivo ID {device_index}: {device_name}")
                else:
                    logger.warning(f"Dispositivo ID {self.config.audio.device_id} inválido")

            elif self.config.audio.device_name:
                device_index = self.device_manager.find_input_device_by_name(self.config.audio.device_name)
                if device_index is not None:
                    device_name = self.config.audio.device_name
                    logger.info(f"Usando dispositivo por nome: {device_name}")
                else:
                    logger.warning(f"Dispositivo '{self.config.audio.device_name}' não encontrado")

            # Configura dispositivo padrão se encontrado
            if device_index is not None:
                self.device_manager.set_default_device(device_index)

            # Cria captura de áudio
            capture_class = VADAudioCapture if self.config.transcription.use_vad else AudioCapture

            if self.config.transcription.use_vad:
                self.audio_capture = capture_class(
                    sample_rate=self.config.audio.sample_rate,
                    channels=self.config.audio.channels,
                    buffer_seconds=self.config.audio.buffer_seconds,
                    device_index=device_index,
                    vad_aggressiveness=self.config.transcription.vad_aggressiveness
                )
            else:
                self.audio_capture = capture_class(
                    sample_rate=self.config.audio.sample_rate,
                    channels=self.config.audio.channels,
                    buffer_seconds=self.config.audio.buffer_seconds,
                    device_index=device_index
                )

            # Atualiza UI com nome do dispositivo
            if self.ui:
                self.ui.set_audio_device(device_name)

            return True

        except Exception as e:
            logger.error(f"Erro ao configurar áudio: {e}")
            return False

    def _setup_transcription(self) -> bool:
        """Configura sistema de transcrição"""
        try:
            self.transcriber = WhisperTranscriber(
                model_name=self.config.transcription.model_name,
                device=self.config.transcription.device,
                language=self.config.transcription.language
            )

            logger.info("Sistema de transcrição configurado")
            return True

        except Exception as e:
            logger.error(f"Erro ao configurar transcrição: {e}")
            return False

    def _setup_translation(self) -> bool:
        """Configura sistema de tradução"""
        try:
            if self.config.translation.enabled:
                self.translation_manager = TranslationManager(
                    mode=self.config.translation.mode,
                    target_language=self.config.translation.target_language
                )

                if self.translation_manager.is_available():
                    logger.info(f"Sistema de tradução configurado: {self.config.translation.mode}")
                else:
                    logger.warning("Nenhum tradutor disponível")
                    self.translation_manager = None
            else:
                logger.info("Tradução desabilitada")
                self.translation_manager = None

            return True

        except Exception as e:
            logger.error(f"Erro ao configurar tradução: {e}")
            return False

    def _setup_ui(self) -> bool:
        """Configura interface do usuário"""
        try:
            if not self.use_simple_ui:
                from .ui.interactive import InteractiveConsole
                self.ui = InteractiveConsole(self.config)
                logger.info("Interface interativa configurada")
            else:
                from .ui.simple import SimpleConsole
                self.ui = SimpleConsole(self.config)
                logger.info("Modo console simples")

            return True

        except Exception as e:
            logger.error(f"Erro ao configurar UI: {e}")
            return False

    def _audio_monitor_loop(self):
        """Loop de monitoramento de áudio"""
        last_transcription_time = 0

        while not self.stop_event.is_set():
            try:
                # Verifica se é hora de processar áudio
                current_time = time.time()
                if current_time - last_transcription_time < self.config.audio.chunk_seconds:
                    time.sleep(0.1)
                    continue

                # Obtém chunk de áudio
                audio_chunk = self.audio_capture.get_audio_chunk(self.config.audio.chunk_seconds)

                if audio_chunk is None or len(audio_chunk) == 0:
                    time.sleep(0.1)
                    continue

                # Atualiza nível de áudio na UI
                if self.ui:
                    audio_level = self.audio_capture.get_audio_level()
                    self.ui.update_audio_level(audio_level)

                # Verifica se há atividade de voz
                if isinstance(self.audio_capture, VADAudioCapture):
                    if not self.audio_capture.has_speech(audio_chunk):
                        continue
                else:
                    if self.audio_capture.is_silent(self.config.audio.silence_threshold):
                        continue

                # Processa transcrição
                self._process_transcription(audio_chunk)
                last_transcription_time = current_time

            except Exception as e:
                logger.error(f"Erro no loop de áudio: {e}")
                time.sleep(1)

    def _process_transcription(self, audio_data: np.ndarray):
        """Processa transcrição de áudio"""
        try:
            # Transcreve
            result = self.transcriber.transcribe_audio(audio_data, self.config.audio.sample_rate)

            if result is None or not result.text.strip():
                return

            original_text = result.text.strip()

            # Mostra resultado imediatamente (sem tradução)
            timestamp = time.strftime('%H:%M:%S')

            if self.ui:
                # Adiciona à interface interativa sem tradução primeiro
                self.ui.add_transcription(
                    text=original_text,
                    language=result.language,
                    confidence=getattr(result, 'confidence', 0.0),
                    translation=None
                )

                # Inicia tradução assíncrona se habilitada
                if self.translation_manager:
                    def translate_async():
                        try:
                            translation_result = self.translation_manager.translate(original_text, result.language)
                            if translation_result:
                                # Atualiza a última transcrição com a tradução
                                self.ui.update_last_translation(translation_result.translated_text)
                        except Exception as e:
                            logger.error(f"Erro na tradução assíncrona: {e}")

                    translation_thread = threading.Thread(target=translate_async, daemon=True)
                    translation_thread.start()
            else:
                # Modo console simples - tradução síncrona
                translated_text = None
                if self.translation_manager:
                    translation_result = self.translation_manager.translate(original_text, result.language)
                    if translation_result:
                        translated_text = translation_result.translated_text

                if translated_text:
                    print(f"\n[{timestamp}] {original_text} ➜ {translated_text}")
                else:
                    print(f"\n[{timestamp}] {original_text}")

        except Exception as e:
            logger.error(f"Erro no processamento de transcrição: {e}")

    def list_devices(self):
        """Lista dispositivos de áudio disponíveis"""
        self.device_manager.print_devices()

    def start(self) -> bool:
        """Inicia a aplicação"""
        if self.is_running:
            logger.warning("Aplicação já está rodando")
            return False

        logger.info("Iniciando Whisper Transcriber...")

        # Setup dos componentes
        if not self._setup_audio():
            return False

        if not self._setup_transcription():
            return False

        if not self._setup_translation():
            return False

        if not self._setup_ui():
            return False

        # Inicia captura de áudio
        if not self.audio_capture.start():
            logger.error("Falha ao iniciar captura de áudio")
            return False

        self.is_running = True
        self.stop_event.clear()

        # Inicia UI
        if self.ui:
            self.ui_thread = threading.Thread(target=self.ui.start, daemon=True)
            self.ui_thread.start()

        self.audio_monitor_thread = threading.Thread(target=self._audio_monitor_loop, daemon=True)
        self.audio_monitor_thread.start()

        logger.info("✅ Aplicação iniciada com sucesso!")

        if not self.ui:
            print("🎙️ Captura contínua de áudio... (Ctrl+C para parar)")
            print("="*50)

        return True

    def stop(self):
        """Para a aplicação"""
        if not self.is_running:
            return

        logger.info("Parando aplicação...")
        self.stop_event.set()
        self.is_running = False

        # Para captura de áudio
        if self.audio_capture:
            self.audio_capture.stop()

        # Para UI
        if self.ui:
            self.ui.stop()

        # Aguarda threads
        if self.audio_monitor_thread and self.audio_monitor_thread.is_alive():
            self.audio_monitor_thread.join(timeout=2)

        if self.ui_thread and self.ui_thread.is_alive():
            self.ui_thread.join(timeout=2)

        logger.info("✅ Aplicação finalizada")

    def run(self):
        """Executa aplicação (blocking)"""
        if not self.start():
            return False

        try:
            # Mantém aplicação viva
            if self.ui:
                # Com UI interativa, aguarda UI thread
                if self.ui_thread:
                    self.ui_thread.join()
            else:
                # Modo console simples, aguarda Ctrl+C
                while self.is_running and not self.stop_event.is_set():
                    time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\nInterrupção por teclado recebida")

        finally:
            self.stop()

        return True


def create_app(use_simple_ui=False) -> WhisperApplication:
    """Factory function para criar aplicação"""
    return WhisperApplication(use_simple_ui=use_simple_ui)
