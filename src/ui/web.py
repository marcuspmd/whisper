"""
Interface web para Whisper Transcriber usando Flask.
"""

import os
import json
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from flask import Flask, render_template, jsonify, request, send_from_directory
from waitress import serve
import logging

logger = logging.getLogger(__name__)

@dataclass
class WebTranscriptionEntry:
    """Entrada de transcrição para interface web."""
    id: str
    timestamp: str
    text: str
    language: str
    confidence: float = 0.0
    translation: Optional[str] = None
    audio_level: float = 0.0

class WebInterface:
    """Interface web usando Flask."""

    def __init__(self, config, transcription_manager=None):
        self.config = config
        self.transcription_manager = transcription_manager
        self.app = Flask(__name__,
                        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                        static_folder=os.path.join(os.path.dirname(__file__), 'static'))

        # Dados da aplicação
        self.transcriptions: List[WebTranscriptionEntry] = []
        self.current_stats = {
            'total_transcriptions': 0,
            'languages_detected': {},
            'translation_count': 0,
            'current_audio_level': 0.0,
            'uptime_seconds': 0,
            'status': 'stopped'
        }
        self.start_time = datetime.now()
        # token simples para shutdown remoto (opcional)
        self._shutdown_token = f"token_{int(time.time())}"
        self._on_shutdown = None
        self._server = None  # Referência ao servidor Waitress
        self._shutdown_event = threading.Event()
        self._setup_routes()

    def _setup_routes(self):
        """Configura rotas Flask."""

        @self.app.route('/')
        def index():
            """Página principal."""
            return render_template('index.html')

        @self.app.route('/api/transcriptions')
        def get_transcriptions():
            """API: Retorna transcrições recentes."""
            limit = request.args.get('limit', 50, type=int)
            return jsonify([asdict(t) for t in self.transcriptions[-limit:]])

        @self.app.route('/api/stats')
        def get_stats():
            """API: Retorna estatísticas da aplicação."""
            self.current_stats['uptime_seconds'] = int((datetime.now() - self.start_time).total_seconds())
            return jsonify(self.current_stats)

        @self.app.route('/api/config')
        def get_config():
            """API: Retorna configuração atual."""
            if self.config:
                return jsonify({
                    'model': getattr(self.config.transcription, 'model_name', 'unknown'),
                    'language': getattr(self.config.transcription, 'language', 'auto'),
                    'device_id': getattr(self.config.audio, 'device_index', None),
                    'sample_rate': getattr(self.config.audio, 'sample_rate', 16000),
                    'translation_enabled': getattr(self.config.translation, 'enabled', False),
                    'translation_target': getattr(self.config.translation, 'target_language', 'pt')
                })
            return jsonify({})

        @self.app.route('/api/clear')
        def clear_transcriptions():
            """API: Limpa transcrições."""
            self.transcriptions.clear()
            self.current_stats['total_transcriptions'] = 0
            self.current_stats['languages_detected'] = {}
            self.current_stats['translation_count'] = 0
            return jsonify({'status': 'cleared'})

        @self.app.route('/api/shutdown', methods=['POST'])
        def api_shutdown():
            """Shutdown seguro do servidor via token (POST: {'token': '...'})"""
            try:
                payload = request.get_json(force=True)
            except Exception:
                return jsonify({'error': 'invalid payload'}), 400

            token = payload.get('token') if isinstance(payload, dict) else None
            if token != self._shutdown_token:
                return jsonify({'error': 'unauthorized'}), 401

            # chama callback de shutdown se existir
            if self._on_shutdown:
                try:
                    threading.Thread(target=self._on_shutdown, daemon=True).start()
                except Exception as e:
                    logger.error(f"Erro ao chamar on_shutdown: {e}")

            # sinaliza shutdown e agenda parada do servidor
            self._shutdown_event.set()

            def delayed_shutdown():
                time.sleep(0.5)  # permite que a resposta seja enviada
                if self._server:
                    try:
                        self._server.close()
                    except Exception as e:
                        logger.error(f"Erro ao fechar servidor: {e}")

            threading.Thread(target=delayed_shutdown, daemon=True).start()

            # responde antes de parar
            return jsonify({'status': 'shutting down'})

    def add_transcription(self, text: str, language: str, confidence: float = 0.0,
                         translation: Optional[str] = None, audio_level: float = 0.0):
        """Adiciona nova transcrição."""
        entry = WebTranscriptionEntry(
            id=f"trans_{int(time.time() * 1000)}",
            timestamp=datetime.now().strftime("%H:%M:%S"),
            text=text,
            language=language,
            confidence=confidence,
            translation=translation,
            audio_level=audio_level
        )

        self.transcriptions.append(entry)

        # Limita histórico a 1000 entradas
        if len(self.transcriptions) > 1000:
            self.transcriptions = self.transcriptions[-1000:]

        # Atualiza estatísticas
        self.current_stats['total_transcriptions'] = len(self.transcriptions)

        if language in self.current_stats['languages_detected']:
            self.current_stats['languages_detected'][language] += 1
        else:
            self.current_stats['languages_detected'][language] = 1

        if translation:
            self.current_stats['translation_count'] += 1

        logger.debug(f"Nova transcrição adicionada: {text[:50]}...")

    def update_last_translation(self, translation: str):
        """Atualiza a tradução da última transcrição."""
        if self.transcriptions:
            self.transcriptions[-1].translation = translation
            self.current_stats['translation_count'] += 1
            logger.debug(f"Tradução atualizada: {translation[:50]}...")

    def update_audio_level(self, level: float):
        """Atualiza nível de áudio atual."""
        self.current_stats['current_audio_level'] = level

    def update_status(self, status: str):
        """Atualiza status da aplicação."""
        self.current_stats['status'] = status

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Inicia servidor Waitress (mais estável que Flask dev server)."""
        logger.info(f"Iniciando interface web com Waitress em http://{host}:{port}")
        self.update_status('running')

        try:
            # Usa Waitress em vez do Flask dev server para melhor signal handling
            serve(self.app, host=host, port=port, threads=6)
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor web: {e}")
            self.update_status('error')

    def stop(self):
        """Para o servidor."""
        self.update_status('stopped')
        self._shutdown_event.set()
        if self._server:
            try:
                self._server.close()
            except Exception as e:
                logger.error(f"Erro ao fechar servidor: {e}")
        logger.info("Interface web parada")

    def set_on_shutdown(self, callback):
        """Define callback a ser chamado quando /api/shutdown for acionado."""
        self._on_shutdown = callback

    def get_shutdown_token(self) -> str:
        """Retorna o token atual de shutdown (útil para operações internas)."""
        return self._shutdown_token
