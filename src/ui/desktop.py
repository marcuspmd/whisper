"""
Interface desktop usando Tkinter para Whisper Transcriber.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DesktopInterface:
    """Interface desktop usando Tkinter."""

    def __init__(self, config, transcription_manager=None):
        self.config = config
        self.transcription_manager = transcription_manager
        self.app = None  # WhisperApplication será definida depois

        # Estado da interface
        self.is_running = False
        self.current_stats = {
            'total_transcriptions': 0,
            'languages_detected': {},
            'translation_count': 0,
            'current_audio_level': 0.0,
            'uptime_seconds': 0,
            'status': 'stopped'
        }
        self.start_time = None

        # Criar janela principal
        self.root = tk.Tk()
        self.root.title("Whisper Transcriber")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # Configurar fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface do usuário."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar redimensionamento
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Título
        title_label = ttk.Label(main_frame, text="🎙️ Whisper Transcriber",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # Frame de controles
        controls_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        controls_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        controls_frame.columnconfigure(2, weight=1)

        # Botões
        self.start_button = ttk.Button(controls_frame, text="▶️ Iniciar",
                                      command=self.start_transcription)
        self.start_button.grid(row=0, column=0, padx=(0, 5))

        self.stop_button = ttk.Button(controls_frame, text="⏹️ Parar",
                                     command=self.stop_transcription, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)

        # Status
        self.status_var = tk.StringVar(value="Parado")
        status_label = ttk.Label(controls_frame, text="Status:")
        status_label.grid(row=0, column=2, padx=(20, 5), sticky=tk.E)

        self.status_display = ttk.Label(controls_frame, textvariable=self.status_var,
                                       foreground="red")
        self.status_display.grid(row=0, column=3, sticky=tk.W)

        # Nível de áudio
        audio_label = ttk.Label(controls_frame, text="Áudio:")
        audio_label.grid(row=1, column=0, padx=(0, 5), pady=(10, 0), sticky=tk.W)

        self.audio_level_var = tk.DoubleVar()
        self.audio_progressbar = ttk.Progressbar(controls_frame, variable=self.audio_level_var,
                                               maximum=100, length=200)
        self.audio_progressbar.grid(row=1, column=1, columnspan=2, pady=(10, 0),
                                   padx=5, sticky=(tk.W, tk.E))

        self.audio_level_label = ttk.Label(controls_frame, text="0%")
        self.audio_level_label.grid(row=1, column=3, pady=(10, 0), sticky=tk.W)

        # Frame de transcrições
        transcriptions_frame = ttk.LabelFrame(main_frame, text="Transcrições", padding="10")
        transcriptions_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        transcriptions_frame.columnconfigure(0, weight=1)
        transcriptions_frame.rowconfigure(0, weight=1)

        # Área de texto para transcrições
        self.transcriptions_text = scrolledtext.ScrolledText(
            transcriptions_frame,
            wrap=tk.WORD,
            height=15,
            font=("Arial", 10)
        )
        self.transcriptions_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame de informações
        info_frame = ttk.LabelFrame(main_frame, text="Informações", padding="10")
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        # Estatísticas
        self.stats_var = tk.StringVar(value="Total: 0 transcrições")
        stats_label = ttk.Label(info_frame, textvariable=self.stats_var)
        stats_label.grid(row=0, column=0, sticky=tk.W)

        # Configurações atuais
        config_info = self._get_config_info()
        config_label = ttk.Label(info_frame, text=config_info, font=("Arial", 8))
        config_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # Botões de ação
        clear_button = ttk.Button(info_frame, text="🗑️ Limpar",
                                 command=self.clear_transcriptions)
        clear_button.grid(row=0, column=1, padx=(10, 0))

        # Iniciar thread de atualização da UI
        self._start_ui_updater()

    def _get_config_info(self) -> str:
        """Retorna informações de configuração formatadas."""
        if not self.config:
            return "Configuração não disponível"

        model = getattr(self.config.transcription, 'model_name', 'unknown')
        device = getattr(self.config.audio, 'device_index', 'auto')
        lang = getattr(self.config.transcription, 'language', 'auto')
        translate = getattr(self.config.translation, 'enabled', False)

        return f"Modelo: {model} | Dispositivo: {device} | Idioma: {lang} | Tradução: {'Sim' if translate else 'Não'}"

    def _start_ui_updater(self):
        """Inicia thread para atualizar UI periodicamente."""
        def update_loop():
            while True:
                try:
                    # Atualizar a cada 100ms
                    self.root.after(100, self._update_ui_elements)
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Erro no loop de atualização da UI: {e}")

        update_thread = threading.Thread(target=update_loop, daemon=True)
        update_thread.start()

    def _update_ui_elements(self):
        """Atualiza elementos da UI no thread principal."""
        try:
            # Atualizar estatísticas
            stats_text = f"Total: {self.current_stats['total_transcriptions']} transcrições"
            if self.current_stats['translation_count'] > 0:
                stats_text += f" | Traduções: {self.current_stats['translation_count']}"
            if self.current_stats['uptime_seconds'] > 0:
                mins = self.current_stats['uptime_seconds'] // 60
                secs = self.current_stats['uptime_seconds'] % 60
                stats_text += f" | Tempo: {mins:02d}:{secs:02d}"

            self.stats_var.set(stats_text)

            # Atualizar nível de áudio
            level = self.current_stats['current_audio_level']
            self.audio_level_var.set(level)
            self.audio_level_label.config(text=f"{level:.0f}%")

            # Atualizar cor da barra de áudio
            if level > 80:
                style = "red.Horizontal.TProgressbar"
            elif level > 50:
                style = "yellow.Horizontal.TProgressbar"
            else:
                style = "green.Horizontal.TProgressbar"

            # Atualizar tempo de execução
            if self.is_running and self.start_time:
                self.current_stats['uptime_seconds'] = int((datetime.now() - self.start_time).total_seconds())

        except Exception as e:
            logger.error(f"Erro ao atualizar UI: {e}")

    def start_transcription(self):
        """Inicia a transcrição."""
        if self.is_running or not self.app:
            return

        try:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_var.set("Iniciando...")
            self.status_display.config(foreground="orange")

            # Iniciar aplicação em thread separada
            def start_app():
                try:
                    self.app.start()
                    self.root.after(0, lambda: self._on_app_started())
                except Exception as e:
                    logger.error(f"Erro ao iniciar aplicação: {e}")
                    self.root.after(0, lambda: self._on_app_error(str(e)))

            app_thread = threading.Thread(target=start_app, daemon=True)
            app_thread.start()

        except Exception as e:
            logger.error(f"Erro ao iniciar transcrição: {e}")
            self._on_app_error(str(e))

    def _on_app_started(self):
        """Callback quando app inicia com sucesso."""
        self.is_running = True
        self.start_time = datetime.now()
        self.status_var.set("Executando")
        self.status_display.config(foreground="green")
        self.current_stats['status'] = 'running'

    def _on_app_error(self, error_msg: str):
        """Callback quando há erro na app."""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_var.set("Erro")
        self.status_display.config(foreground="red")
        messagebox.showerror("Erro", f"Erro ao iniciar transcrição:\n{error_msg}")

    def stop_transcription(self):
        """Para a transcrição."""
        if not self.is_running or not self.app:
            return

        try:
            self.stop_button.config(state="disabled")
            self.status_var.set("Parando...")
            self.status_display.config(foreground="orange")

            # Parar aplicação em thread separada
            def stop_app():
                try:
                    self.app.stop()
                    self.root.after(0, lambda: self._on_app_stopped())
                except Exception as e:
                    logger.error(f"Erro ao parar aplicação: {e}")
                    self.root.after(0, lambda: self._on_app_stopped())

            stop_thread = threading.Thread(target=stop_app, daemon=True)
            stop_thread.start()

        except Exception as e:
            logger.error(f"Erro ao parar transcrição: {e}")
            self._on_app_stopped()

    def _on_app_stopped(self):
        """Callback quando app para."""
        self.is_running = False
        self.start_time = None
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_var.set("Parado")
        self.status_display.config(foreground="red")
        self.current_stats['status'] = 'stopped'
        self.current_stats['current_audio_level'] = 0.0
        self.audio_level_var.set(0)

    def clear_transcriptions(self):
        """Limpa área de transcrições."""
        self.transcriptions_text.delete(1.0, tk.END)
        self.current_stats['total_transcriptions'] = 0
        self.current_stats['languages_detected'] = {}
        self.current_stats['translation_count'] = 0

    def add_transcription(self, text: str, language: str, confidence: float = 0.0,
                         translation: Optional[str] = None, audio_level: float = 0.0):
        """Adiciona nova transcrição à interface."""
        def update_ui():
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Formatar entrada
            entry = f"[{timestamp}] ({language}) {text}"
            if translation:
                entry += f"\n    → {translation}"
            entry += "\n\n"

            # Adicionar ao texto
            self.transcriptions_text.insert(tk.END, entry)
            self.transcriptions_text.see(tk.END)  # Auto-scroll

            # Atualizar estatísticas
            self.current_stats['total_transcriptions'] += 1

            if language in self.current_stats['languages_detected']:
                self.current_stats['languages_detected'][language] += 1
            else:
                self.current_stats['languages_detected'][language] = 1

            if translation:
                self.current_stats['translation_count'] += 1

        self.root.after(0, update_ui)

    def update_last_translation(self, translation: str):
        """Atualiza tradução da última entrada."""
        def update_ui():
            # Buscar última linha com transcrição
            content = self.transcriptions_text.get(1.0, tk.END)
            lines = content.split('\n')

            # Encontrar última entrada e adicionar tradução
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith('[') and ']' in lines[i]:
                    # Inserir tradução após a linha encontrada
                    insert_pos = f"{i+2}.0"
                    self.transcriptions_text.insert(insert_pos, f"    → {translation}\n")
                    self.transcriptions_text.see(tk.END)
                    break

            self.current_stats['translation_count'] += 1

        self.root.after(0, update_ui)

    def update_audio_level(self, level: float):
        """Atualiza nível de áudio."""
        self.current_stats['current_audio_level'] = level

    def update_status(self, status: str):
        """Atualiza status da aplicação."""
        self.current_stats['status'] = status

    def set_app(self, app):
        """Define a aplicação Whisper."""
        self.app = app

    def run(self):
        """Executa a interface."""
        try:
            logger.info("Iniciando interface desktop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Erro na interface desktop: {e}")

    def stop(self):
        """Para a interface."""
        if self.is_running:
            self.stop_transcription()
        self.root.quit()

    def on_closing(self):
        """Callback para fechamento da janela."""
        if self.is_running:
            if messagebox.askokcancel("Sair", "Transcrição está ativa. Deseja parar e sair?"):
                self.stop_transcription()
                self.root.after(1000, self.root.destroy)  # Aguarda 1s para parar
        else:
            self.root.destroy()
