"""
Configuration management and settings
"""
import os
import json
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Configurações de áudio"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_seconds: int = 3
    buffer_seconds: int = 15
    overlap_seconds: int = 1
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    silence_threshold: float = 50.0
    tail_check_ms: int = 120
    lookahead_seconds: Optional[float] = None


@dataclass
class TranscriptionConfig:
    """Configurações de transcrição"""
    model_name: str = "base"
    device: str = "cpu"
    compute_type: str = "int8"
    language: Optional[str] = None
    use_vad: bool = False
    vad_aggressiveness: int = 2


@dataclass
class TranslationConfig:
    """Configurações de tradução"""
    enabled: bool = True
    mode: str = "local"  # "local" ou "google"
    target_language: str = "pt"
    model_name: str = "Helsinki-NLP/opus-mt-en-pt"


@dataclass
class UIConfig:
    """Configurações de interface"""
    log_level: str = "INFO"
    colored_logs: bool = True
    interactive_mode: bool = True
    refresh_rate: int = 10  # Hz
    max_recent_texts: int = 10


@dataclass
class AppConfig:
    """Configuração completa da aplicação"""

    def __init__(self):
        self.audio = AudioConfig()
        self.transcription = TranscriptionConfig()
        self.translation = TranslationConfig()
        self.ui = UIConfig()


class ConfigManager:
    """Gerenciador de configurações"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = os.path.expanduser("~/.whisper-transcriber")

        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.yaml"
        self.config = AppConfig()

        # Cria diretório se não existir
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Carrega configurações
        self.load()

    def load(self) -> None:
        """Carrega configurações do arquivo"""
        if not self.config_file.exists():
            logger.info("Arquivo de configuração não encontrado, usando padrões")
            self.save()  # Salva configurações padrão
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data:
                self._update_config_from_dict(data)

            logger.info(f"Configurações carregadas de {self.config_file}")

        except Exception as e:
            logger.error(f"Erro ao carregar configurações: {e}")
            logger.info("Usando configurações padrão")

    def save(self) -> None:
        """Salva configurações no arquivo"""
        try:
            data = {
                'audio': asdict(self.config.audio),
                'transcription': asdict(self.config.transcription),
                'translation': asdict(self.config.translation),
                'ui': asdict(self.config.ui)
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"Configurações salvas em {self.config_file}")

        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {e}")

    def _update_config_from_dict(self, data: Dict[str, Any]) -> None:
        """Atualiza configuração a partir de dicionário"""
        try:
            if 'audio' in data:
                for key, value in data['audio'].items():
                    if hasattr(self.config.audio, key):
                        setattr(self.config.audio, key, value)

            if 'transcription' in data:
                for key, value in data['transcription'].items():
                    if hasattr(self.config.transcription, key):
                        setattr(self.config.transcription, key, value)

            if 'translation' in data:
                for key, value in data['translation'].items():
                    if hasattr(self.config.translation, key):
                        setattr(self.config.translation, key, value)

            if 'ui' in data:
                for key, value in data['ui'].items():
                    if hasattr(self.config.ui, key):
                        setattr(self.config.ui, key, value)

        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")


# Instância global do gerenciador de configuração
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Obtém instância global do gerenciador de configuração"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Obtém configuração atual"""
    return get_config_manager().config
