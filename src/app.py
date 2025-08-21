"""
Main application orchestrator
"""

import logging
import multiprocessing as mp
import os
import signal
import sys
import threading
import time
# Suprimir warnings do pkg_resources
import warnings
from typing import Optional

import numpy as np

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
    )

from .audio.capture import AudioCapture, VADAudioCapture
from .audio.device_manager import AudioDeviceManager
from .config.settings import get_config_manager
from .transcription.whisper_engine import WhisperTranscriber
from .translation.engines import TranslationManager
from .ui.simple import create_interactive_console
from .utils.logger import setup_colored_logging

logger = logging.getLogger(__name__)


class WhisperApplication:
    """Aplicação principal de transcrição"""

    def __init__(self, use_simple_ui=False, headless=False):
        self.config_manager = get_config_manager()
        self.config = self.config_manager.config
        self.use_simple_ui = use_simple_ui
        self.headless = headless

        # Componentes principais
        self.device_manager = AudioDeviceManager()
        self.audio_capture = None
        self.transcriber = None
        self.translation_manager = None
        self.ui = None
        self.web_interface = None
        self.desktop_interface = None

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
        import logging
        import os
        from logging.handlers import RotatingFileHandler

        # Remove todos os handlers existentes
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Cria diretório de logs se não existir
        log_dir = os.path.expanduser("~/.whisper-transcriber/logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")

        # Configura apenas logging para arquivo para evitar interferir com a interface
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Configura root logger
        root_logger.setLevel(getattr(logging, self.config.ui.log_level))
        root_logger.addHandler(file_handler)

        # Log inicial para confirmar que está funcionando
        logger.info("Sistema de logging configurado - logs em arquivo apenas")

    def _setup_signal_handlers(self):
        """Configura handlers de sinais para parada limpa."""
        self._shutdown_in_progress = False

        def signal_handler(signum, frame):
            if self._shutdown_in_progress:
                logger.warning("Shutdown já em progresso, ignorando sinal adicional")
                return

            self._shutdown_in_progress = True
            signal_name = signal.Signals(signum).name
            logger.info(f"Sinal {signal_name} recebido, iniciando parada...")

            # Força exit após timeout se não conseguir parar normalmente
            def force_exit():
                logger.warning("Timeout de shutdown atingido, forçando saída...")
                import os

                os._exit(1)

            # Timer de 10 segundos para força exit
            import threading

            timer = threading.Timer(10.0, force_exit)
            timer.start()

            try:
                self.stop()
                timer.cancel()  # Cancela timer se conseguiu parar normalmente
            except Exception as e:
                logger.error(f"Erro durante stop(): {e}")
                # Timer vai executar e forçar saída

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _setup_audio(self) -> bool:
        """Configura captura de áudio"""
        try:
            # Seleciona dispositivo
            device_index = None
            device_name = "Dispositivo padrão"

            if self.config.audio.device_id is not None:
                device_info = self.device_manager.find_device_by_id(
                    self.config.audio.device_id
                )
                if device_info and device_info[2] > 0:  # tem entrada
                    device_index = device_info[0]
                    device_name = device_info[1]
                    logger.info(f"Usando dispositivo ID {device_index}: {device_name}")
                else:
                    logger.warning(
                        f"Dispositivo ID {self.config.audio.device_id} inválido"
                    )

            elif self.config.audio.device_name:
                device_index = self.device_manager.find_input_device_by_name(
                    self.config.audio.device_name
                )
                if device_index is not None:
                    device_name = self.config.audio.device_name
                    logger.info(f"Usando dispositivo por nome: {device_name}")
                else:
                    logger.warning(
                        f"Dispositivo '{self.config.audio.device_name}' não encontrado"
                    )

            # Configura dispositivo padrão se encontrado
            if device_index is not None:
                self.device_manager.set_default_device(device_index)

            # Cria captura de áudio
            capture_class = (
                VADAudioCapture if self.config.transcription.use_vad else AudioCapture
            )

            if self.config.transcription.use_vad:
                self.audio_capture = capture_class(
                    sample_rate=self.config.audio.sample_rate,
                    channels=self.config.audio.channels,
                    buffer_seconds=self.config.audio.buffer_seconds,
                    device_index=device_index,
                    vad_aggressiveness=self.config.transcription.vad_aggressiveness,
                )
            else:
                self.audio_capture = capture_class(
                    sample_rate=self.config.audio.sample_rate,
                    channels=self.config.audio.channels,
                    buffer_seconds=self.config.audio.buffer_seconds,
                    device_index=device_index,
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
                language=self.config.transcription.language,
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
                    target_language=self.config.translation.target_language,
                )

                if self.translation_manager.is_available():
                    logger.info(
                        f"Sistema de tradução configurado: {self.config.translation.mode}"
                    )
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
            if self.headless:
                # Modo headless - sem interface terminal
                self.ui = None
                logger.info("Modo headless - sem interface terminal")
            elif not self.use_simple_ui:
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

    def set_web_interface(self, web_interface):
        """Define interface web para comunicação."""
        self.web_interface = web_interface
        logger.info("Interface web conectada")

    def set_desktop_interface(self, desktop_interface):
        """Define interface desktop para comunicação."""
        self.desktop_interface = desktop_interface
        logger.info("Interface desktop conectada")

    def _audio_monitor_loop(self):
        """Loop de monitoramento de áudio"""
        last_transcription_time = 0
        speech_start_time = None

        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                # Se VAD está ativo, usa lógica diferente
                if isinstance(self.audio_capture, VADAudioCapture):
                    # Obtém chunk pequeno para detecção rápida
                    detection_chunk = self.audio_capture.get_audio_chunk(
                        0.5
                    )  # 500ms para detecção

                    if detection_chunk is None or len(detection_chunk) == 0:
                        time.sleep(0.1)
                        continue

                    # Atualiza nível de áudio
                    audio_level = self.audio_capture.get_audio_level()
                    if self.ui:
                        self.ui.update_audio_level(audio_level)
                    if self.web_interface:
                        self.web_interface.update_audio_level(audio_level)
                    if self.desktop_interface:
                        self.desktop_interface.update_audio_level(audio_level)

                    # Verifica se há fala
                    if self.audio_capture.has_speech(detection_chunk):
                        if speech_start_time is None:
                            speech_start_time = current_time

                        # Aguarda acumular pelo menos 2 segundos de fala antes de transcrever
                        if current_time - speech_start_time >= 2.0:
                            # Cooldown: aguarda pelo menos 1 segundo desde a última transcrição
                            if current_time - last_transcription_time >= 1.0:
                                # Obtém chunk maior para transcrição
                                chunk_duration = getattr(
                                    self.config.audio, "vad_chunk_seconds", 2.5
                                )
                                audio_chunk = self.audio_capture.get_audio_chunk(
                                    chunk_duration
                                )

                                if audio_chunk is not None and len(audio_chunk) > 0:
                                    self._process_transcription(audio_chunk)
                                    last_transcription_time = current_time
                                    speech_start_time = (
                                        None  # Reset para próxima detecção
                                    )
                    else:
                        # Sem fala detectada
                        if speech_start_time is not None:
                            # Se estava falando e parou, aguarda um pouco antes de resetar
                            if current_time - speech_start_time >= 3.0:
                                speech_start_time = None

                    time.sleep(0.1)  # Verifica a cada 100ms

                else:
                    # Lógica original para modo sem VAD
                    if (
                        current_time - last_transcription_time
                        < self.config.audio.chunk_seconds
                    ):
                        time.sleep(0.1)
                        continue

                    # Obtém chunk de áudio
                    audio_chunk = self.audio_capture.get_audio_chunk(
                        self.config.audio.chunk_seconds
                    )

                    if audio_chunk is None or len(audio_chunk) == 0:
                        time.sleep(0.1)
                        continue

                    # Atualiza nível de áudio
                    audio_level = self.audio_capture.get_audio_level()
                    if self.ui:
                        self.ui.update_audio_level(audio_level)
                    if self.web_interface:
                        self.web_interface.update_audio_level(audio_level)
                    if self.desktop_interface:
                        self.desktop_interface.update_audio_level(audio_level)

                    # Verifica se há atividade de voz
                    if self.audio_capture.is_silent(
                        self.config.audio.silence_threshold
                    ):
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
            result = self.transcriber.transcribe_audio(
                audio_data, self.config.audio.sample_rate
            )

            if result is None or not result.text.strip():
                return

            original_text = result.text.strip()

            # Mostra resultado imediatamente (sem tradução)
            timestamp = time.strftime("%H:%M:%S")
            confidence = getattr(result, "confidence", 0.0)
            current_audio_level = (
                self.audio_capture.get_audio_level() if self.audio_capture else 0.0
            )

            # Adiciona à interface terminal se disponível
            if self.ui:
                self.ui.add_transcription(
                    text=original_text,
                    language=result.language,
                    confidence=confidence,
                    translation=None,
                )

            # Adiciona à interface web se disponível
            if self.web_interface:
                self.web_interface.add_transcription(
                    text=original_text,
                    language=result.language,
                    confidence=confidence,
                    translation=None,
                    audio_level=current_audio_level,
                )

            # Adiciona à interface desktop se disponível
            if self.desktop_interface:
                self.desktop_interface.add_transcription(
                    text=original_text,
                    language=result.language,
                    confidence=confidence,
                    translation=None,
                    audio_level=current_audio_level,
                )

                # Inicia tradução assíncrona se habilitada
                if self.translation_manager:

                    def translate_async():
                        try:
                            translation_result = self.translation_manager.translate(
                                original_text, result.language
                            )
                            if translation_result:
                                # Atualiza a última transcrição com a tradução
                                if self.ui:
                                    self.ui.update_last_translation(
                                        translation_result.translated_text
                                    )
                                if self.web_interface:
                                    self.web_interface.update_last_translation(
                                        translation_result.translated_text
                                    )
                                if self.desktop_interface:
                                    self.desktop_interface.update_last_translation(
                                        translation_result.translated_text
                                    )
                        except Exception as e:
                            logger.error(f"Erro na tradução assíncrona: {e}")

                    translation_thread = threading.Thread(
                        target=translate_async, daemon=True
                    )
                    translation_thread.start()
            else:
                # Modo console simples - tradução síncrona
                translated_text = None
                if self.translation_manager:
                    translation_result = self.translation_manager.translate(
                        original_text, result.language
                    )
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

        self.audio_monitor_thread = threading.Thread(
            target=self._audio_monitor_loop, daemon=True
        )
        self.audio_monitor_thread.start()

        logger.info("✅ Aplicação iniciada com sucesso!")

        if not self.ui:
            print("🎙️ Captura contínua de áudio... (Ctrl+C para parar)")
            print("=" * 50)

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


def create_app(use_simple_ui=False, headless=False) -> WhisperApplication:
    """Factory function para criar aplicação"""
    return WhisperApplication(use_simple_ui=use_simple_ui, headless=headless)
