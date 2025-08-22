"""
Correções para problemas de perda de áudio durante transcrição
"""

import logging
import queue
import threading
import time
import os
from datetime import datetime
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class AsyncTranscriptionProcessor:
    """Processador assíncrono de transcrição para evitar perda de áudio"""

    def __init__(self, transcriber, translation_manager=None, ui=None, desktop_interface=None):
        self.transcriber = transcriber
        self.translation_manager = translation_manager
        self.ui = ui
        self.desktop_interface = desktop_interface

        # Queue para processamento assíncrono
        self.audio_queue = queue.Queue(maxsize=10)  # Máximo 10 chunks aguardando
        self.result_queue = queue.Queue()

        # Thread de processamento
        self.processing_thread = None
        self.is_running = False

        # Sistema de backup de transcrição
        self._setup_transcription_backup()

    def _setup_transcription_backup(self):
        """Configura sistema de backup de transcrição"""
        backup_dir = os.path.expanduser("~/.whisper-transcriber/backups")
        os.makedirs(backup_dir, exist_ok=True)

        # Nome do arquivo baseado no timestamp da sessão
        session_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_file = os.path.join(backup_dir, f"transcription_{session_time}.txt")

        # Arquivo temporário para transcrição em andamento
        self.temp_file = os.path.join(backup_dir, "current_transcription.txt")

        # Inicializa arquivos
        with open(self.backup_file, "w", encoding="utf-8") as f:
            f.write(f"=== Sessão de Transcrição - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

        with open(self.temp_file, "w", encoding="utf-8") as f:
            f.write(f"=== Transcrição Atual - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")

        logger.info(f"Backup de transcrição configurado: {self.backup_file}")

    def _save_transcription(self, text: str, translation: str = None):
        """Salva transcrição nos arquivos de backup"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            entry = f"[{timestamp}] {text}\n"

            if translation:
                entry += f"[{timestamp}] (Tradução) {translation}\n"

            entry += "\n"

            # Salva no arquivo da sessão
            with open(self.backup_file, "a", encoding="utf-8") as f:
                f.write(entry)

            # Atualiza arquivo temporário (mantém só as últimas 20 entradas)
            with open(self.temp_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Mantém header + últimas 60 linhas (aprox. 20 entradas)
            header_lines = lines[:2]  # Header
            recent_lines = lines[-58:] if len(lines) > 60 else lines[2:]

            with open(self.temp_file, "w", encoding="utf-8") as f:
                f.writelines(header_lines)
                f.writelines(recent_lines)
                f.write(entry)

        except Exception as e:
            logger.error(f"Erro ao salvar backup de transcrição: {e}")

    def start(self):
        """Inicia processador assíncrono"""
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        logger.info("Processador assíncrono de transcrição iniciado")

    def stop(self):
        """Para processador assíncrono"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
        logger.info("Processador assíncrono de transcrição parado")

    def add_audio_chunk(self, audio_data: np.ndarray, sample_rate: int) -> bool:
        """
        Adiciona chunk de áudio para processamento assíncrono

        Returns:
            True se adicionado com sucesso, False se queue está cheia
        """
        try:
            # Adiciona com timeout para evitar bloqueio
            self.audio_queue.put((audio_data, sample_rate), timeout=0.1)
            return True
        except queue.Full:
            logger.warning("Queue de transcrição cheia - descartando chunk de áudio")
            return False

    def _processing_loop(self):
        """Loop principal de processamento de transcrição"""
        while self.is_running:
            try:
                # Obtém próximo chunk com timeout
                audio_data, sample_rate = self.audio_queue.get(timeout=1.0)

                # Processa transcrição
                self._process_transcription_chunk(audio_data, sample_rate)

                # Marca como processado
                self.audio_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erro no processamento assíncrono: {e}")
                time.sleep(0.1)

    def _process_transcription_chunk(self, audio_data: np.ndarray, sample_rate: int):
        """Processa um chunk de transcrição"""
        try:
            # Transcreve (pode ser demorado)
            result = self.transcriber.transcribe_audio(audio_data, sample_rate)

            if result is None or not result.text.strip():
                return

            original_text = result.text.strip()
            timestamp = time.strftime("%H:%M:%S")
            confidence = getattr(result, "confidence", 0.0)

            # Salva no backup imediatamente
            self._save_transcription(original_text)

            # Adiciona às interfaces imediatamente (sem tradução)
            if self.ui:
                self.ui.add_transcription(
                    original=original_text,
                    language=result.language,
                    translated=None
                )

            if self.desktop_interface:
                self.desktop_interface.add_transcription(
                    text=original_text,
                    language=result.language,
                    confidence=confidence,
                    translation=None,
                    audio_level=0.0
                )

            # Inicia tradução assíncrona se habilitada
            if self.translation_manager:
                translation_thread = threading.Thread(
                    target=self._translate_async,
                    args=(original_text, result.language),
                    daemon=True
                )
                translation_thread.start()

        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")

    def _translate_async(self, original_text: str, language: str):
        """Traduz texto de forma assíncrona"""
        try:
            translation_result = self.translation_manager.translate(original_text, language)
            if translation_result:
                translated_text = translation_result.translated_text

                # Salva tradução no backup
                self._save_transcription(original_text, translated_text)

                # Atualiza interfaces com tradução
                if self.ui:
                    self.ui.update_last_translation(translated_text)

                if self.desktop_interface:
                    self.desktop_interface.update_last_translation(translated_text)

        except Exception as e:
            logger.error(f"Erro na tradução assíncrona: {e}")

    def get_queue_size(self) -> int:
        """Retorna tamanho atual da queue"""
        return self.audio_queue.qsize()
