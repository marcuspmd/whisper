"""
Whisper transcription engine
"""
import os
import tempfile
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from typing import Optional, List
from collections import deque
import logging

logger = logging.getLogger(__name__)


class TranscriptionResult:
    """Resultado de transcrição"""
    
    def __init__(self, text: str, language: Optional[str] = None, confidence: Optional[float] = None):
        self.text = text
        self.language = language
        self.confidence = confidence
        self.timestamp = None
    
    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return f"TranscriptionResult(text='{self.text}', language='{self.language}')"


class WhisperTranscriber:
    """Motor de transcrição usando Whisper"""
    
    def __init__(
        self,
        model_name: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = None
    ):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.model = None
        self.recent_texts = deque(maxlen=5)
        
        self._load_model()
    
    def _load_model(self) -> None:
        """Carrega o modelo Whisper"""
        try:
            logger.info(f"Carregando modelo Whisper: {self.model_name}")
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info("Modelo carregado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            raise
    
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int) -> Optional[TranscriptionResult]:
        """
        Transcreve áudio.
        
        Args:
            audio_data: Dados de áudio como array numpy
            sample_rate: Taxa de amostragem
            
        Returns:
            Resultado da transcrição ou None se erro
        """
        if self.model is None:
            logger.error("Modelo não carregado")
            return None
        
        if len(audio_data) == 0:
            return None
        
        # Salva áudio temporário
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                temp_path = tmp.name
                sf.write(temp_path, audio_data, sample_rate, subtype='PCM_16')
            
            # Parâmetros de transcrição otimizados para tempo real
            transcribe_params = {
                "beam_size": 1,
                "best_of": 1,
                "temperature": 0.0,
                "condition_on_previous_text": False
            }
            
            if self.language:
                transcribe_params['language'] = self.language
            
            # Transcreve
            segments, info = self.model.transcribe(temp_path, **transcribe_params)
            
            # Processa segmentos
            for segment in segments:
                text = getattr(segment, 'text', '').strip()
                if not text:
                    continue
                
                # Evita repetições
                if text.lower() in [r.lower() for r in self.recent_texts]:
                    continue
                
                self.recent_texts.append(text)
                
                return TranscriptionResult(
                    text=text,
                    language=getattr(info, 'language', None),
                    confidence=getattr(segment, 'avg_logprob', None)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            return None
        
        finally:
            # Limpa arquivo temporário
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo temporário: {e}")
    
    def set_language(self, language: Optional[str]) -> None:
        """Define idioma para transcrição"""
        self.language = language
        logger.info(f"Idioma definido para: {language or 'auto-detect'}")
    
    def get_supported_languages(self) -> List[str]:
        """Retorna lista de idiomas suportados"""
        return [
            'en', 'pt', 'es', 'fr', 'de', 'it', 'ja', 'ko', 'zh', 'ru',
            'ar', 'tr', 'pl', 'nl', 'sv', 'da', 'no', 'fi', 'cs', 'sk'
        ]


def create_transcriber(
    model_name: str = "base",
    device: str = "cpu",
    language: Optional[str] = None
) -> WhisperTranscriber:
    """Factory function para criar transcriber"""
    return WhisperTranscriber(
        model_name=model_name,
        device=device,
        language=language
    )
