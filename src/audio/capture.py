"""
Audio capture module
"""
import numpy as np
import sounddevice as sd
import threading
import queue
import time
from collections import deque
from typing import Callable, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AudioBuffer:
    """Buffer circular thread-safe para áudio"""

    def __init__(self, max_seconds: int, sample_rate: int):
        self.max_samples = max_seconds * sample_rate
        self.sample_rate = sample_rate
        self.buffer = deque(maxlen=self.max_samples)
        self.lock = threading.Lock()

    def add_samples(self, samples: np.ndarray) -> None:
        """Adiciona amostras ao buffer"""
        with self.lock:
            self.buffer.extend(samples)

    def get_samples(self, num_samples: int) -> np.ndarray:
        """Obtém últimas N amostras do buffer"""
        with self.lock:
            if len(self.buffer) < num_samples:
                return np.array([], dtype=np.int16)

            # Converte para array as últimas N amostras
            samples = list(self.buffer)[-num_samples:]
            return np.array(samples, dtype=np.int16)

    def get_buffer_duration(self) -> float:
        """Retorna duração atual do buffer em segundos"""
        with self.lock:
            return len(self.buffer) / self.sample_rate

    def clear(self) -> None:
        """Limpa o buffer"""
        with self.lock:
            self.buffer.clear()


class AudioCapture:
    """Gerencia captura contínua de áudio"""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        buffer_seconds: int = 15,
        device_index: Optional[int] = None,
        callback: Optional[Callable[[np.ndarray], None]] = None
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self.callback = callback

        self.buffer = AudioBuffer(buffer_seconds, sample_rate)
        self.stream = None
        self.is_recording = False
        self.stop_flag = threading.Event()

        # Configurações de captura
        self.block_size = int(0.1 * sample_rate)  # 100ms blocks (reduzido de 200ms)
        self.audio_level = 0.0
        self._level_lock = threading.Lock()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: Any, status: sd.CallbackFlags) -> None:
        """Callback chamado pelo sounddevice"""
        try:
            if status:
                logger.warning(f"Audio callback status: {status}")

            # Primeiro canal apenas
            raw_audio = indata[:, 0]

            # Normaliza para range -1 a 1 se necessário
            if raw_audio.dtype != np.float64 or np.abs(raw_audio).max() > 1.0:
                # Converte de int16 para float64 normalizado
                if raw_audio.dtype == np.int16:
                    raw_audio_normalized = raw_audio.astype(np.float64) / 32768.0
                else:
                    # Normaliza pelo valor máximo presente
                    max_val = np.abs(raw_audio).max()
                    if max_val > 0:
                        raw_audio_normalized = raw_audio / max_val
                    else:
                        raw_audio_normalized = raw_audio
            else:
                raw_audio_normalized = raw_audio

            # Normalização mais suave para evitar "explosão"
            audio_data = (raw_audio_normalized * 32767 * 0.8).astype(np.int16)  # 80% do range para margem

            # Adiciona ao buffer
            self.buffer.add_samples(audio_data)

            # Atualiza nível de áudio de forma thread-safe
            with self._level_lock:
                # Calcula RMS dos dados normalizados (-1 a 1)
                rms = np.sqrt(np.mean(raw_audio_normalized ** 2))
                # Normaliza para 0-1 com multiplicador adequado para voz humana
                self.audio_level = min(1.0, rms * 15)  # Ajustado para sensibilidade adequada

            # Chama callback externo se definido
            if self.callback:
                try:
                    self.callback(audio_data)
                except Exception as e:
                    logger.error(f"Erro no callback externo: {e}")

        except Exception as e:
            logger.error(f"Erro no callback de áudio: {e}")

    def start(self) -> bool:
        """
        Inicia captura de áudio.

        Returns:
            True se sucesso, False caso contrário
        """
        if self.is_recording:
            logger.warning("Captura já está ativa")
            return True

        try:
            self.stream = sd.InputStream(
                callback=self._audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype='int16',
                device=self.device_index,
                blocksize=self.block_size,
                latency='low'
            )

            self.stream.start()
            self.is_recording = True
            self.stop_flag.clear()

            logger.info(f"Captura iniciada - dispositivo: {self.device_index or 'padrão'}")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar captura: {e}")
            return False

    def stop(self) -> None:
        """Para a captura de áudio"""
        if not self.is_recording:
            return

        self.stop_flag.set()
        self.is_recording = False

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.error(f"Erro ao parar stream: {e}")
            finally:
                self.stream = None

        logger.info("Captura parada")

    def get_audio_chunk(self, duration_seconds: float) -> Optional[np.ndarray]:
        """
        Obtém chunk de áudio com duração especificada.

        Args:
            duration_seconds: Duração em segundos

        Returns:
            Array numpy com áudio ou None se insuficiente
        """
        if not self.is_recording:
            return None

        num_samples = int(duration_seconds * self.sample_rate)
        return self.buffer.get_samples(num_samples)

    def get_audio_level(self) -> float:
        """
        Retorna nível RMS atual do áudio.

        Returns:
            Nível RMS normalizado (0.0-1.0)
        """
        with self._level_lock:
            return self.audio_level

    def is_silent(self, threshold: float = 50.0, duration_ms: int = 100) -> bool:
        """
        Verifica se o áudio está silencioso.

        Args:
            threshold: Limiar RMS para considerar silêncio
            duration_ms: Duração para verificar silêncio

        Returns:
            True se silencioso
        """
        samples_to_check = int(duration_ms / 1000.0 * self.sample_rate)
        recent_audio = self.buffer.get_samples(samples_to_check)

        if len(recent_audio) == 0:
            return True

        rms = np.sqrt(np.mean(recent_audio.astype(float) ** 2))
        return rms < threshold

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


class VADAudioCapture(AudioCapture):
    """Captura de áudio com Voice Activity Detection"""

    def __init__(self, *args, vad_aggressiveness: int = 2, **kwargs):
        super().__init__(*args, **kwargs)
        self.vad = None
        self.vad_aggressiveness = vad_aggressiveness

        # Tenta carregar webrtcvad
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(vad_aggressiveness)
            logger.info(f"VAD carregado com agressividade {vad_aggressiveness}")
        except ImportError:
            logger.warning("webrtcvad não disponível, usando detecção RMS")

    def has_speech(self, audio_data: np.ndarray) -> bool:
        """
        Detecta se há fala no áudio usando VAD.

        Sensibilidade VAD:
        - 0: Muito conservador (só fala muito clara)
        - 1: Conservador (fala clara)
        - 2: Moderado (padrão - boa balance)
        - 3: Agressivo (detecta sussurros e ruído baixo)

        Args:
            audio_data: Dados de áudio

        Returns:
            True se detectar fala
        """
        if self.vad is None:
            # Fallback para RMS - ajustado baseado na agressividade
            rms = np.sqrt(np.mean(audio_data.astype(float) ** 2))
            # Limiares baseados na agressividade do VAD
            thresholds = {0: 35.0, 1: 25.0, 2: 18.0, 3: 12.0}
            threshold = thresholds.get(self.vad_aggressiveness, 18.0)
            return rms > threshold

        # WebRTC VAD requer frames de 10, 20 ou 30ms
        frame_ms = 30
        frame_len = int(self.sample_rate * frame_ms / 1000)

        if len(audio_data) < frame_len:
            return False

        # Analisa frames sem overlap para evitar detecções excessivas
        speech_frames = 0
        total_frames = 0

        # Divide o áudio em frames sequenciais (sem overlap)
        for i in range(0, len(audio_data) - frame_len + 1, frame_len):
            frame = audio_data[i:i + frame_len]
            if len(frame) < frame_len:
                continue

            total_frames += 1
            try:
                if self.vad.is_speech(frame.tobytes(), self.sample_rate):
                    speech_frames += 1
            except Exception:
                # Se falhar, usa RMS como fallback para este frame
                rms = np.sqrt(np.mean(frame.astype(float) ** 2))
                thresholds = {0: 35.0, 1: 25.0, 2: 18.0, 3: 12.0}
                threshold = thresholds.get(self.vad_aggressiveness, 18.0)
                if rms > threshold:
                    speech_frames += 1

        # Critério mais conservador baseado na agressividade
        if total_frames == 0:
            return False

        speech_ratio = speech_frames / total_frames

        # Limiares de speech_ratio baseados na agressividade
        ratio_thresholds = {
            0: 0.6,   # 60% dos frames devem ter fala (muito conservador)
            1: 0.4,   # 40% dos frames devem ter fala (conservador)
            2: 0.25,  # 25% dos frames devem ter fala (moderado)
            3: 0.15   # 15% dos frames devem ter fala (agressivo)
        }

        threshold = ratio_thresholds.get(self.vad_aggressiveness, 0.25)
        return speech_ratio >= threshold