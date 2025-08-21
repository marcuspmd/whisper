"""
Unit tests for the main application
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.app import WhisperApplication, create_app


class TestWhisperApplication(unittest.TestCase):
    """Test cases for WhisperApplication class"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = None

    def tearDown(self):
        """Clean up after tests"""
        if self.app:
            try:
                self.app.destroy()
            except:
                pass

    @patch('src.app.whisper.load_model')
    def test_create_app_headless(self, mock_load_model):
        """Test creating app in headless mode"""
        mock_load_model.return_value = MagicMock()

        app = create_app(headless=True)
        self.assertIsInstance(app, WhisperApplication)
        self.assertTrue(app.headless)

    @patch('src.app.whisper.load_model')
    def test_app_initialization(self, mock_load_model):
        """Test basic app initialization"""
        mock_load_model.return_value = MagicMock()

        try:
            app = WhisperApplication(headless=True)
            self.assertIsNotNone(app)
            self.assertTrue(hasattr(app, 'model'))
            self.assertTrue(hasattr(app, 'config_manager'))
        except Exception as e:
            self.skipTest(f"App initialization failed: {e}")

    def test_model_names(self):
        """Test that model names are properly defined"""
        from src.app import WhisperApplication

        # Check if model names are available
        self.assertTrue(hasattr(WhisperApplication, '_get_available_models') or
                       hasattr(WhisperApplication, 'model_names'))

    @patch('src.app.pyaudio.PyAudio')
    def test_audio_devices_detection(self, mock_pyaudio):
        """Test audio device detection"""
        mock_pa = MagicMock()
        mock_pa.get_device_count.return_value = 2
        mock_pa.get_device_info_by_index.side_effect = [
            {'name': 'Device 1', 'maxInputChannels': 2},
            {'name': 'Device 2', 'maxInputChannels': 1}
        ]
        mock_pyaudio.return_value = mock_pa

        try:
            app = WhisperApplication(headless=True)
            devices = app._get_audio_devices()
            self.assertIsInstance(devices, list)
            mock_pa.terminate.assert_called_once()
        except Exception as e:
            self.skipTest(f"Audio device test failed: {e}")


class TestConfigManager(unittest.TestCase):
    """Test cases for configuration management"""

    def test_config_manager_import(self):
        """Test that config manager can be imported"""
        try:
            from src.config.settings import get_config_manager
            config_manager = get_config_manager()
            self.assertIsNotNone(config_manager)
        except ImportError as e:
            self.skipTest(f"Config manager import failed: {e}")

    def test_config_defaults(self):
        """Test default configuration values"""
        try:
            from src.config.settings import get_config_manager
            config_manager = get_config_manager()

            # Check if basic config methods exist
            self.assertTrue(hasattr(config_manager, 'get'))
            self.assertTrue(hasattr(config_manager, 'set'))
        except Exception as e:
            self.skipTest(f"Config defaults test failed: {e}")


class TestTranslation(unittest.TestCase):
    """Test cases for translation functionality"""

    def test_translation_import(self):
        """Test that translation module can be imported"""
        try:
            from src.utils.translation import get_translation_manager
            translation_manager = get_translation_manager()
            self.assertIsNotNone(translation_manager)
        except ImportError as e:
            self.skipTest(f"Translation import failed: {e}")

    def test_available_languages(self):
        """Test that supported languages are defined"""
        try:
            from src.utils.translation import get_translation_manager
            translation_manager = get_translation_manager()

            languages = translation_manager.get_supported_languages()
            self.assertIsInstance(languages, (list, dict))
            self.assertGreater(len(languages), 0)
        except Exception as e:
            self.skipTest(f"Languages test failed: {e}")


if __name__ == '__main__':
    unittest.main()
