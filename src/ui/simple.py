"""
Simple console interface fallback
"""

import logging
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SimpleConsole:
    """Console simples sem rich"""

    def __init__(self):
        self.transcriptions = deque(maxlen=10)
        self.stats = {
            "total_transcriptions": 0,
            "total_words": 0,
            "session_start": datetime.now(),
            "last_activity": None,
        }
        self.audio_level = 0.0
        self.is_silent = True
        self.device_name = "Dispositivo padrão"
        self.is_running = False

    def add_transcription(
        self,
        original: str,
        translated: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """Adiciona nova transcrição"""
        timestamp = datetime.now()

        # Atualiza estatísticas
        self.stats["total_transcriptions"] += 1
        self.stats["total_words"] += len(original.split())
        self.stats["last_activity"] = timestamp

        # Exibe resultado
        timestamp_str = timestamp.strftime("%H:%M:%S")
        if translated:
            print(f"\n[{timestamp_str}] {original} ➜ {translated}")
        else:
            print(f"\n[{timestamp_str}] {original}")

    def update_audio_level(self, level: float, is_silent: bool = False):
        """Atualiza nível de áudio"""
        self.audio_level = level
        self.is_silent = is_silent

    def set_audio_device(self, device_name: str):
        """Define dispositivo de áudio"""
        self.device_name = device_name
        print(f"🎵 Dispositivo de áudio: {device_name}")

    def show_welcome(self):
        """Mostra tela de boas-vindas"""
        print("\n" + "=" * 60)
        print("🎙️  WHISPER REAL-TIME TRANSCRIBER v2.0")
        print("=" * 60)
        print("Transcrição e tradução em tempo real")
        print("\n🎵 Monitor de áudio em tempo real")
        print("📝 Histórico de transcrições")
        print("🌐 Tradução automática")
        print("⚙️ Configurações persistentes")
        print("\nPressione Ctrl+C para sair")
        print("=" * 60)

    def start(self):
        """Inicia interface"""
        if self.is_running:
            return

        self.show_welcome()
        self.is_running = True

    def stop(self):
        """Para interface"""
        self.is_running = False
        print("\n" + "=" * 60)

        # Mostra estatísticas finais
        session_duration = datetime.now() - self.stats["session_start"]
        hours, remainder = divmod(int(session_duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        print("📊 ESTATÍSTICAS DA SESSÃO")
        print("-" * 30)
        print(f"⏱️  Tempo de sessão: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print(f"📝 Total de transcrições: {self.stats['total_transcriptions']}")
        print(f"💬 Total de palavras: {self.stats['total_words']}")
        print("\n👋 Até logo!")
        print("=" * 60)

    def run_in_thread(self) -> threading.Thread:
        """Executa interface em thread separada"""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread

    def set_transcription_callback(self, callback: Callable):
        """Define callback para novas transcrições (compatibilidade)"""
        pass

    def set_config_change_callback(self, callback: Callable):
        """Define callback para mudanças de configuração (compatibilidade)"""
        pass


def create_interactive_console():
    """Factory function para criar console"""
    # Tenta usar Rich primeiro, fallback para console simples
    try:
        # Se rich foi instalado, importa a versão completa
        import rich

        from .interactive_rich import InteractiveConsole

        logger.info("Usando interface Rich")
        return InteractiveConsole()
    except ImportError:
        logger.info("Rich não disponível, usando console simples")
        return SimpleConsole()
