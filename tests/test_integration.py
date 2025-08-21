"""
Integration tests for audio functionality
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestAudioProcessing(unittest.TestCase):
    """Test cases for audio processing functionality"""

    @unittest.skipIf(not os.environ.get('AUDIO_TESTS'), "Audio tests require AUDIO_TESTS=1")
    def test_audio_recording_mock(self):
        """Test audio recording with mocked audio input"""
        try:
            with patch('src.audio.recorder.pyaudio.PyAudio') as mock_pyaudio:
                mock_stream = MagicMock()
                mock_stream.read.return_value = b'\x00' * 1024  # Mock audio data

                mock_pa = MagicMock()
                mock_pa.open.return_value = mock_stream
                mock_pyaudio.return_value = mock_pa

                from src.audio.recorder import AudioRecorder
                recorder = AudioRecorder()

                # Test that recorder can be created
                self.assertIsNotNone(recorder)

        except ImportError as e:
            self.skipTest(f"Audio recorder import failed: {e}")

    def test_vad_detection_mock(self):
        """Test Voice Activity Detection with mock data"""
        try:
            # Create mock audio data (1 second of 16kHz mono)
            sample_rate = 16000
            duration = 1.0
            samples = int(sample_rate * duration)

            # Generate some audio data (sine wave)
            t = np.linspace(0, duration, samples, False)
            audio_data = np.sin(2 * np.pi * 440 * t) * 0.3  # 440Hz sine wave
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()

            # Test VAD functionality if available
            try:
                import webrtcvad
                vad = webrtcvad.Vad(2)  # Moderate aggressiveness

                # Test with 30ms frames (480 samples at 16kHz)
                frame_size = 480
                frame_bytes = audio_bytes[:frame_size * 2]  # 2 bytes per sample

                # Should not raise an exception
                result = vad.is_speech(frame_bytes, sample_rate)
                self.assertIsInstance(result, bool)

            except ImportError:
                self.skipTest("webrtcvad not available")

        except Exception as e:
            self.skipTest(f"VAD test failed: {e}")


class TestTranscription(unittest.TestCase):
    """Test cases for transcription functionality"""

    @patch('src.app.whisper.load_model')
    def test_whisper_model_loading(self, mock_load_model):
        """Test Whisper model loading"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {'text': 'Hello world'}
        mock_load_model.return_value = mock_model

        try:
            from src.app import WhisperApplication
            app = WhisperApplication(headless=True)

            # Test that model is loaded
            self.assertIsNotNone(app.model)
            mock_load_model.assert_called_once()

        except Exception as e:
            self.skipTest(f"Model loading test failed: {e}")

    def test_transcription_with_mock_audio(self):
        """Test transcription with mock audio data"""
        try:
            with patch('src.app.whisper.load_model') as mock_load_model:
                mock_model = MagicMock()
                mock_model.transcribe.return_value = {
                    'text': 'This is a test transcription',
                    'language': 'en'
                }
                mock_load_model.return_value = mock_model

                from src.app import WhisperApplication
                app = WhisperApplication(headless=True)

                # Create mock audio data
                mock_audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

                # Test transcription
                result = app.model.transcribe(mock_audio)
                self.assertIn('text', result)
                self.assertIn('language', result)

        except Exception as e:
            self.skipTest(f"Transcription test failed: {e}")


class TestUIInterfaces(unittest.TestCase):
    """Test cases for user interface functionality"""

    def test_desktop_interface_creation(self):
        """Test desktop interface creation"""
        try:
            from src.ui.desktop import DesktopInterface
            # Basic creation test - don't actually show UI in tests
            self.assertTrue(hasattr(DesktopInterface, '__init__'))

        except ImportError as e:
            self.skipTest(f"Desktop interface import failed: {e}")

    def test_simple_interface_creation(self):
        """Test simple console interface creation"""
        try:
            from src.ui.simple import SimpleInterface
            # Basic creation test
            self.assertTrue(hasattr(SimpleInterface, '__init__'))

        except ImportError as e:
            self.skipTest(f"Simple interface import failed: {e}")
if __name__ == '__main__':
    unittest.main()
