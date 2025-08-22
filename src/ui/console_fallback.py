"""
Console minimalista para fallback quando GUI não está disponível
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ConsoleFallback:
    """Interface console extremamente simples para casos de emergência"""

    def __init__(self, config=None):
        self.config = config
        self.is_running = False
        print("🎤 Whisper Transcriber - Modo Console")
        print("Pressione Ctrl+C para sair")

    def add_transcription(
        self,
        original: str,
        translated: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """Adiciona nova transcrição"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if translated:
            print(f"[{timestamp}] {original} ➜ {translated}")
        else:
            print(f"[{timestamp}] {original}")

    def update_audio_level(self, level: float):
        """Atualiza nível de áudio (ignorado no console)"""
        pass

    def update_silence_status(self, is_silent: bool):
        """Atualiza status de silêncio (ignorado no console)"""
        pass

    def update_device_name(self, name: str):
        """Atualiza nome do dispositivo"""
        pass

    def set_audio_device(self, name: str):
        """Define dispositivo de áudio (compatibilidade)"""
        pass

    def update_last_translation(self, translation: str):
        """Atualiza última tradução (compatibilidade)"""
        pass

    def start(self):
        """Inicia interface"""
        self.is_running = True
        try:
            # Aguarda infinitamente (será interrompido por Ctrl+C)
            import time
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def stop(self):
        """Para interface"""
        self.is_running = False
