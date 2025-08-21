"""
Translation engines and utilities
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TranslationResult:
    """Resultado de tradução"""

    def __init__(self, translated_text: str, source_language: Optional[str] = None, target_language: str = "pt"):
        self.translated_text = translated_text
        self.source_language = source_language
        self.target_language = target_language
        self.confidence = None

    def __str__(self) -> str:
        return self.translated_text


class BaseTranslator(ABC):
    """Interface base para tradutores"""

    def __init__(self, target_language: str = "pt"):
        self.target_language = target_language
        self.cache = {}  # Cache simples de traduções

    @abstractmethod
    def translate(self, text: str, source_language: Optional[str] = None) -> Optional[TranslationResult]:
        """Traduz texto"""
        pass

    def _get_cache_key(self, text: str, source_lang: Optional[str]) -> str:
        """Gera chave para cache"""
        return f"{source_lang or 'auto'}_{self.target_language}_{text}"

    def _get_cached(self, text: str, source_language: Optional[str]) -> Optional[TranslationResult]:
        """Obtém tradução do cache"""
        key = self._get_cache_key(text, source_language)
        return self.cache.get(key)

    def _cache_result(self, text: str, source_language: Optional[str], result: TranslationResult) -> None:
        """Armazena resultado no cache"""
        key = self._get_cache_key(text, source_language)
        self.cache[key] = result


class GoogleTranslator(BaseTranslator):
    """Tradutor usando Google Translate"""

    def __init__(self, target_language: str = "pt"):
        super().__init__(target_language)
        self.translator = None
        self._initialize()

    def _initialize(self) -> None:
        """Inicializa o tradutor Google"""
        try:
            from googletrans import Translator
            self.translator = Translator()
            logger.info("Google Translator inicializado")
        except ImportError:
            logger.error("googletrans não disponível")
            raise
        except Exception as e:
            logger.error(f"Erro ao inicializar Google Translator: {e}")
            raise

    def translate(self, text: str, source_language: Optional[str] = None) -> Optional[TranslationResult]:
        """
        Traduz texto usando Google Translate.

        Args:
            text: Texto para traduzir
            source_language: Idioma de origem (auto-detect se None)

        Returns:
            Resultado da tradução ou None se erro
        """
        if not text.strip():
            return None

        # Verifica cache
        cached = self._get_cached(text, source_language)
        if cached:
            return cached

        if self.translator is None:
            logger.error("Tradutor não inicializado")
            return None

        try:
            result = self.translator.translate(
                text,
                dest=self.target_language,
                src=source_language or 'auto'
            )

            translation_result = TranslationResult(
                translated_text=result.text,
                source_language=result.src,
                target_language=self.target_language
            )

            # Cache resultado
            self._cache_result(text, source_language, translation_result)

            return translation_result

        except Exception as e:
            logger.error(f"Erro na tradução Google: {e}")
            return None


class LocalTranslator(BaseTranslator):
    """Tradutor local usando transformers"""

    def __init__(self, target_language: str = "pt", model_name: str = "Helsinki-NLP/opus-mt-en-pt"):
        super().__init__(target_language)
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self._initialize()

    def _initialize(self) -> None:
        """Inicializa modelo local"""
        try:
            from transformers import MarianMTModel, MarianTokenizer

            logger.info(f"Carregando modelo local: {self.model_name}")
            self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
            self.model = MarianMTModel.from_pretrained(self.model_name)
            logger.info("Modelo local carregado com sucesso")

        except ImportError:
            logger.error("transformers não disponível")
            raise
        except Exception as e:
            logger.error(f"Erro ao carregar modelo local: {e}")
            raise

    def translate(self, text: str, source_language: Optional[str] = None) -> Optional[TranslationResult]:
        """
        Traduz texto usando modelo local.

        Args:
            text: Texto para traduzir
            source_language: Idioma de origem (ignorado no modelo local)

        Returns:
            Resultado da tradução ou None se erro
        """
        if not text.strip():
            return None

        # Verifica cache
        cached = self._get_cached(text, source_language)
        if cached:
            return cached

        if self.model is None or self.tokenizer is None:
            logger.error("Modelo local não inicializado")
            return None

        try:
            # Tokeniza
            inputs = self.tokenizer(text, return_tensors='pt', padding=True)

            # Gera tradução
            tokens = self.model.generate(**inputs)

            # Decodifica
            translated = self.tokenizer.decode(tokens[0], skip_special_tokens=True)

            translation_result = TranslationResult(
                translated_text=translated,
                source_language="en",  # Modelo específico en->pt
                target_language=self.target_language
            )

            # Cache resultado
            self._cache_result(text, source_language, translation_result)

            return translation_result

        except Exception as e:
            logger.error(f"Erro na tradução local: {e}")
            return None


class TranslationManager:
    """Gerenciador de tradução com fallbacks"""

    def __init__(self, mode: str = "local", target_language: str = "pt"):
        self.mode = mode
        self.target_language = target_language
        self.primary_translator = None
        self.fallback_translator = None
        self.enabled = True

        self._setup_translators()

    def _setup_translators(self) -> None:
        """Configura tradutores primário e fallback"""
        try:
            if self.mode == "local":
                # Tenta modelo local primeiro
                try:
                    self.primary_translator = LocalTranslator(self.target_language)
                    logger.info("Tradutor local configurado como primário")
                except Exception as e:
                    logger.warning(f"Erro no tradutor local: {e}")
                    self.primary_translator = None

                # Google como fallback
                try:
                    self.fallback_translator = GoogleTranslator(self.target_language)
                    logger.info("Google Translator configurado como fallback")
                except Exception as e:
                    logger.warning(f"Erro no Google Translator: {e}")
                    self.fallback_translator = None

            else:  # mode == "google"
                # Google como primário
                try:
                    self.primary_translator = GoogleTranslator(self.target_language)
                    logger.info("Google Translator configurado como primário")
                except Exception as e:
                    logger.warning(f"Erro no Google Translator: {e}")
                    self.primary_translator = None

        except Exception as e:
            logger.error(f"Erro ao configurar tradutores: {e}")

    def translate(self, text: str, source_language: Optional[str] = None) -> Optional[TranslationResult]:
        """
        Traduz texto usando tradutor disponível.

        Args:
            text: Texto para traduzir
            source_language: Idioma de origem

        Returns:
            Resultado da tradução ou None
        """
        if not self.enabled or not text.strip():
            return None

        # Tenta tradutor primário
        if self.primary_translator:
            try:
                result = self.primary_translator.translate(text, source_language)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Erro no tradutor primário: {e}")

        # Tenta fallback
        if self.fallback_translator:
            try:
                result = self.fallback_translator.translate(text, source_language)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Erro no tradutor fallback: {e}")

        logger.warning("Nenhum tradutor disponível")
        return None

    def set_enabled(self, enabled: bool) -> None:
        """Ativa/desativa tradução"""
        self.enabled = enabled
        logger.info(f"Tradução {'ativada' if enabled else 'desativada'}")

    def is_available(self) -> bool:
        """Verifica se pelo menos um tradutor está disponível"""
        return self.primary_translator is not None or self.fallback_translator is not None


def create_translation_manager(mode: str = "local", target_language: str = "pt") -> TranslationManager:
    """
    Factory function para criar gerenciador de tradução.

    Args:
        mode: Modo de tradução ("local" ou "google")
        target_language: Idioma de destino

    Returns:
        Gerenciador de tradução configurado
    """
    return TranslationManager(mode=mode, target_language=target_language)
