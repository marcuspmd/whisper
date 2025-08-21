"""
Interface desktop usando Tkinter para Whisper Transcriber.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
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

        # Estado de transcrição para ícones
        self.transcription_state = 'idle'  # 'idle', 'listening', 'transcribing', 'silent'

        # Configurações de fonte
        self.font_size = 10
        self.font_family = "Arial"

        # Teleprompter
        self.teleprompter_window = None
        self.teleprompter_text_widget = None

        # Disponibilidade de dispositivos e modelos
        self.available_devices = []
        self.available_models = ['tiny', 'base', 'small', 'medium', 'large']
        self.available_languages = {
            'auto': 'Auto-detectar',
            'pt': 'Português',
            'en': 'Inglês',
            'es': 'Espanhol',
            'fr': 'Francês',
            'de': 'Alemão',
            'it': 'Italiano',
            'ja': 'Japonês',
            'ko': 'Coreano',
            'zh': 'Chinês'
        }

        # Criar janela principal
        self.root = tk.Tk()
        self.root.title("Whisper Transcriber")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        # Configurar fechamento da janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self._load_available_devices()
        self._setup_ui()

    def _load_available_devices(self):
        """Carrega dispositivos de áudio disponíveis."""
        try:
            # Import absoluto para evitar problemas
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            from src.audio.device_manager import AudioDeviceManager
            device_manager = AudioDeviceManager()
            # get_input_devices() agora retorna dispositivos com entrada + virtuais
            devices = device_manager.get_input_devices()

            self.available_devices = []
            for device_id, device_name in devices:
                # Adicionar informação sobre tipo de dispositivo
                device_info = f"{device_id}: {device_name}"

                # Identificar tipos especiais
                name_lower = device_name.lower()
                if any(keyword in name_lower for keyword in ['blackhole', 'loopback', 'soundflower', 'vb-audio', 'voicemeeter']):
                    device_info += " [Virtual Audio]"
                elif any(keyword in name_lower for keyword in ['aggregate', 'agregado', 'combined', 'conjunto']):
                    device_info += " [Dispositivo Agregado]"
                elif any(keyword in name_lower for keyword in ['múltipla', 'multiple', 'multi-output', 'multi output']):
                    device_info += " [Multi-Output Virtual]"
                elif any(keyword in name_lower for keyword in ['obs', 'audio hijack', 'rogue amoeba', 'studio', 'interface']):
                    device_info += " [Software Audio]"
                elif 'macbook' in name_lower or 'built-in' in name_lower:
                    device_info += " [Interno]"
                elif any(keyword in name_lower for keyword in ['usb', 'wireless', 'bluetooth']):
                    device_info += " [Externo]"

                self.available_devices.append((device_id, device_info))

            logger.info(f"Carregados {len(self.available_devices)} dispositivos de áudio (incluindo virtuais)")
            for device_id, device_info in self.available_devices:
                logger.info(f"  - {device_info}")

        except Exception as e:
            logger.error(f"Erro ao carregar dispositivos: {e}")
            # Fallback - criar lista com dispositivo padrão
            self.available_devices = [(None, "Dispositivo padrão do sistema")]

    def _setup_ui(self):
        """Configura a interface do usuário."""
        # Notebook para abas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Aba principal
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="  🎙️ Transcrição  ")

        # Aba de configurações
        config_tab = ttk.Frame(notebook)
        notebook.add(config_tab, text="  ⚙️ Configurações  ")

        self._setup_main_tab(main_tab)
        self._setup_config_tab(config_tab)

    def _setup_main_tab(self, parent):
        """Configura a aba principal."""
        # Frame principal
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Configurar redimensionamento
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Título e opções
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        title_frame.columnconfigure(1, weight=1)

        title_label = ttk.Label(title_frame, text="🎙️ Whisper Transcriber",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)

        # Checkbox para manter janela sempre por cima
        self.always_on_top_var = tk.BooleanVar()
        always_on_top_cb = ttk.Checkbutton(
            title_frame,
            text="📌 Sempre por cima",
            variable=self.always_on_top_var,
            command=self._toggle_always_on_top
        )
        always_on_top_cb.grid(row=0, column=2, sticky=tk.E)

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
            height=12,
            font=(self.font_family, self.font_size)
        )
        self.transcriptions_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame de informações
        info_frame = ttk.LabelFrame(main_frame, text="Informações", padding="10")
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)

        # Primeira linha de informações
        info_row1 = ttk.Frame(info_frame)
        info_row1.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        info_row1.columnconfigure(1, weight=1)

        # Estatísticas
        self.stats_var = tk.StringVar(value="Total: 0 transcrições")
        stats_label = ttk.Label(info_row1, textvariable=self.stats_var)
        stats_label.grid(row=0, column=0, sticky=tk.W)

        # Indicador de estado com ícone
        self.state_var = tk.StringVar(value="😴 Parado")
        state_label = ttk.Label(info_row1, textvariable=self.state_var, font=("Arial", 10, "bold"))
        state_label.grid(row=0, column=1, padx=(20, 0))

        # Segunda linha de informações
        info_row2 = ttk.Frame(info_frame)
        info_row2.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Controles de fonte
        font_label = ttk.Label(info_row2, text="Fonte:")
        font_label.grid(row=0, column=0, sticky=tk.W)

        font_minus_btn = ttk.Button(info_row2, text="A-", width=3,
                                   command=self._decrease_font)
        font_minus_btn.grid(row=0, column=1, padx=(5, 2))

        font_plus_btn = ttk.Button(info_row2, text="A+", width=3,
                                  command=self._increase_font)
        font_plus_btn.grid(row=0, column=2, padx=2)

        self.font_size_var = tk.StringVar(value=f"{self.font_size}pt")
        font_size_label = ttk.Label(info_row2, textvariable=self.font_size_var)
        font_size_label.grid(row=0, column=3, padx=(5, 20))

        # Botões de ação
        clear_button = ttk.Button(info_row2, text="🗑️ Limpar",
                                 command=self.clear_transcriptions)
        clear_button.grid(row=0, column=4, padx=5)

        export_button = ttk.Button(info_row2, text="💾 Exportar",
                                  command=self.export_transcriptions)
        export_button.grid(row=0, column=5)

        teleprompter_button = ttk.Button(info_row2, text="📺 Teleprompter",
                                        command=self.open_teleprompter)
        teleprompter_button.grid(row=0, column=6, padx=(5, 0))

        # Iniciar thread de atualização da UI
        self._start_ui_updater()

    def _setup_config_tab(self, parent):
        """Configura a aba de configurações."""
        config_frame = ttk.Frame(parent, padding="20")
        config_frame.pack(fill="both", expand=True)

        # Título
        title_label = ttk.Label(config_frame, text="⚙️ Configurações de Transcrição",
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)

        row = 1

        # Dispositivo de áudio
        ttk.Label(config_frame, text="🎤 Dispositivo de Áudio:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(config_frame, textvariable=self.device_var,
                                        values=[info for _, info in self.available_devices],
                                        state="readonly", width=40)
        self.device_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)

        # Definir valor atual
        current_device = getattr(self.config.audio, 'device_index', None)
        if current_device is not None:
            for idx, (device_id, device_info) in enumerate(self.available_devices):
                if device_id == current_device:
                    self.device_combo.current(idx)
                    break
        else:
            self.device_combo.current(0)

        row += 1

        # Modelo Whisper
        ttk.Label(config_frame, text="🧠 Modelo Whisper:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(config_frame, textvariable=self.model_var,
                                       values=self.available_models, state="readonly", width=20)
        self.model_combo.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # Definir valor atual
        current_model = getattr(self.config.transcription, 'model_name', 'base')
        try:
            self.model_combo.current(self.available_models.index(current_model))
        except ValueError:
            self.model_combo.current(1)  # base como padrão

        row += 1

        # Idioma
        ttk.Label(config_frame, text="🌍 Idioma do Áudio:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.language_var = tk.StringVar()
        language_values = list(self.available_languages.values())
        self.language_combo = ttk.Combobox(config_frame, textvariable=self.language_var,
                                          values=language_values, state="readonly", width=20)
        self.language_combo.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # Definir valor atual
        current_lang = getattr(self.config.transcription, 'language', None) or 'auto'
        lang_display = self.available_languages.get(current_lang, 'Auto-detectar')
        try:
            self.language_combo.current(language_values.index(lang_display))
        except ValueError:
            self.language_combo.current(0)  # auto como padrão

        row += 1

        # Tradução
        ttk.Label(config_frame, text="🔄 Tradução:").grid(row=row, column=0, sticky=tk.W, pady=5)

        translation_frame = ttk.Frame(config_frame)
        translation_frame.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        self.translation_enabled_var = tk.BooleanVar()
        current_translation = getattr(self.config.translation, 'enabled', False)
        self.translation_enabled_var.set(current_translation)

        translation_cb = ttk.Checkbutton(translation_frame, text="Habilitar tradução",
                                        variable=self.translation_enabled_var,
                                        command=self._toggle_translation)
        translation_cb.grid(row=0, column=0, sticky=tk.W)

        row += 1

        # VAD (Voice Activity Detection)
        ttk.Label(config_frame, text="🎯 Detecção de Voz:").grid(row=row, column=0, sticky=tk.W, pady=5)

        vad_frame = ttk.Frame(config_frame)
        vad_frame.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        self.vad_enabled_var = tk.BooleanVar()
        current_vad = getattr(self.config.transcription, 'use_vad', False)
        self.vad_enabled_var.set(current_vad)

        vad_cb = ttk.Checkbutton(vad_frame, text="Usar detecção por voz (em vez de 3s fixo)",
                                variable=self.vad_enabled_var,
                                command=self._toggle_vad)
        vad_cb.grid(row=0, column=0, sticky=tk.W)

        # Agressividade do VAD
        ttk.Label(vad_frame, text="Sensibilidade:").grid(row=0, column=1, padx=(20, 5), sticky=tk.W)
        self.vad_aggressiveness_var = tk.StringVar()
        vad_aggr_values = ['0 (Baixa)', '1 (Média-baixa)', '2 (Média)', '3 (Alta)']
        self.vad_aggressiveness_combo = ttk.Combobox(vad_frame, textvariable=self.vad_aggressiveness_var,
                                                    values=vad_aggr_values, state="readonly", width=15)
        self.vad_aggressiveness_combo.grid(row=0, column=2, padx=5)

        # Definir valor atual de agressividade
        current_aggr = getattr(self.config.transcription, 'vad_aggressiveness', 2)
        try:
            self.vad_aggressiveness_combo.current(current_aggr)
        except (IndexError, ValueError):
            self.vad_aggressiveness_combo.current(2)  # padrão

        self._toggle_vad()  # Habilitar/desabilitar baseado no estado

        row += 1

        # Idioma de destino para tradução
        ttk.Label(config_frame, text="🎯 Traduzir para:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.target_language_var = tk.StringVar()
        target_language_values = list(self.available_languages.values())
        self.target_language_combo = ttk.Combobox(config_frame, textvariable=self.target_language_var,
                                                 values=target_language_values, state="readonly", width=20)
        self.target_language_combo.grid(row=row, column=1, sticky=tk.W, padx=(10, 0), pady=5)

        # Definir valor atual
        current_target = getattr(self.config.translation, 'target_language', 'pt')
        target_display = self.available_languages.get(current_target, 'Português')
        try:
            self.target_language_combo.current(target_language_values.index(target_display))
        except ValueError:
            self.target_language_combo.current(1)  # português como padrão

        # Habilitar/desabilitar baseado no estado da tradução
        self._toggle_translation()

        row += 2

        # Botão aplicar configurações
        apply_button = ttk.Button(config_frame, text="✅ Aplicar Configurações",
                                 command=self._apply_configuration)
        apply_button.grid(row=row, column=0, columnspan=2, pady=20)

        row += 1

        # Informações atuais
        self.current_config_var = tk.StringVar()
        self.current_config_label = ttk.Label(config_frame, textvariable=self.current_config_var,
                                             font=("Arial", 9), foreground="gray")
        self.current_config_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        self._update_current_config_display()

        # Configurar redimensionamento
        config_frame.columnconfigure(1, weight=1)

    def _toggle_always_on_top(self):
        """Liga/desliga o modo sempre por cima."""
        is_on_top = self.always_on_top_var.get()
        self.root.wm_attributes("-topmost", is_on_top)

    def _increase_font(self):
        """Aumenta o tamanho da fonte."""
        if self.font_size < 20:
            self.font_size += 1
            self._update_font()

    def _decrease_font(self):
        """Diminui o tamanho da fonte."""
        if self.font_size > 8:
            self.font_size -= 1
            self._update_font()

    def _update_font(self):
        """Atualiza a fonte da área de texto."""
        self.transcriptions_text.config(font=(self.font_family, self.font_size))
        self.font_size_var.set(f"{self.font_size}pt")

    def export_transcriptions(self):
        """Exporta as transcrições para um arquivo."""
        from tkinter import filedialog
        import os
        from datetime import datetime

        content = self.transcriptions_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Aviso", "Não há transcrições para exportar.")
            return

        # Sugerir nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"transcricoes_{timestamp}.txt"

        try:
            # Abrir diálogo para salvar
            filename = filedialog.asksaveasfilename(
                title="Exportar Transcrições",
                defaultextension=".txt",
                initialname=default_filename,
                filetypes=[
                    ("Arquivo de Texto", "*.txt"),
                    ("Todos os arquivos", "*.*")
                ]
            )

            if filename:
                # Preparar conteúdo com cabeçalho
                header = f"Transcrições Whisper Transcriber\n"
                header += f"Exportado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}\n"
                header += f"Total de transcrições: {self.current_stats['total_transcriptions']}\n"
                if self.current_stats['translation_count'] > 0:
                    header += f"Total de traduções: {self.current_stats['translation_count']}\n"
                header += "\n" + "="*60 + "\n\n"

                # Salvar arquivo
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(header + content)

                messagebox.showinfo("Sucesso", f"Transcrições exportadas para:\n{filename}")

        except Exception as e:
            logger.error(f"Erro ao exportar transcrições: {e}")
            messagebox.showerror("Erro", f"Erro ao exportar transcrições:\n{e}")

    def _update_transcription_state(self, audio_level: float = 0.0):
        """Atualiza o estado da transcrição baseado no nível de áudio."""
        if not self.is_running:
            self.transcription_state = 'idle'
            self.state_var.set("😴 Parado")
        elif audio_level < 1:  # Muito baixo (ajustado de 5 para 1)
            self.transcription_state = 'silent'
            self.state_var.set("🔇 Sem som")
        elif audio_level < 15:  # Nível baixo (ajustado de 30 para 15)
            self.transcription_state = 'listening'
            self.state_var.set("👂 Ouvindo")
        else:  # Nível detectável, provavelmente transcrevendo
            self.transcription_state = 'transcribing'
            self.state_var.set("🎙️ Transcrevendo")

    def open_teleprompter(self):
        """Abre a janela do teleprompter."""
        if self.teleprompter_window is not None:
            # Se já existe, traz para frente
            self.teleprompter_window.lift()
            self.teleprompter_window.focus()
            return

        # Ocultar GUI principal
        self.root.withdraw()

        # Criar nova janela de teleprompter
        self.teleprompter_window = TeleprompterWindow(self)

    def close_teleprompter(self):
        """Fecha a janela do teleprompter."""
        if self.teleprompter_window:
            self.teleprompter_window.destroy()
            self.teleprompter_window = None
            self.teleprompter_text_widget = None

        # Mostrar GUI principal novamente
        self.root.deiconify()
        self.root.lift()
        self.root.focus()

    def toggle_gui_visibility(self):
        """Alterna visibilidade da GUI principal."""
        if self.teleprompter_window:
            if self.root.state() == 'withdrawn':
                self.root.deiconify()
                self.root.lift()
            else:
                self.root.withdraw()

    def update_teleprompter(self, text: str, translation: Optional[str] = None):
        """Atualiza o texto do teleprompter com timestamp e tradução."""
        if self.teleprompter_text_widget:
            try:
                from datetime import datetime
                timestamp = datetime.now().strftime("%H:%M:%S")

                # Formatar texto com timestamp
                teleprompter_entry = f"[{timestamp}] {text}"
                if translation and translation.strip():
                    teleprompter_entry += f"\n    → {translation}"
                teleprompter_entry += "\n\n"

                self.teleprompter_text_widget.insert(tk.END, teleprompter_entry)
                self.teleprompter_text_widget.see(tk.END)
            except tk.TclError:
                # Janela foi fechada
                self.teleprompter_window = None
                self.teleprompter_text_widget = None

    def _toggle_translation(self):
        """Habilita/desabilita controles de tradução."""
        enabled = self.translation_enabled_var.get()
        state = "readonly" if enabled else "disabled"
        self.target_language_combo.config(state=state)

    def _toggle_vad(self):
        """Habilita/desabilita controles de VAD."""
        enabled = self.vad_enabled_var.get()
        state = "readonly" if enabled else "disabled"
        self.vad_aggressiveness_combo.config(state=state)

    def _apply_configuration(self):
        """Aplica as configurações selecionadas."""
        try:
            # Dispositivo de áudio
            device_text = self.device_var.get()
            for device_id, device_info in self.available_devices:
                if device_info == device_text:
                    self.config.audio.device_index = device_id
                    break

            # Modelo
            self.config.transcription.model_name = self.model_var.get()

            # Idioma
            lang_display = self.language_var.get()
            for lang_code, lang_name in self.available_languages.items():
                if lang_name == lang_display:
                    if lang_code == 'auto':
                        self.config.transcription.language = None
                    else:
                        self.config.transcription.language = lang_code
                    break

            # VAD (Voice Activity Detection)
            self.config.transcription.use_vad = self.vad_enabled_var.get()

            if self.config.transcription.use_vad:
                aggr_text = self.vad_aggressiveness_var.get()
                aggr_level = int(aggr_text.split()[0])  # Pega o número antes do espaço
                self.config.transcription.vad_aggressiveness = aggr_level

            # Tradução
            self.config.translation.enabled = self.translation_enabled_var.get()

            if self.config.translation.enabled:
                target_display = self.target_language_var.get()
                for lang_code, lang_name in self.available_languages.items():
                    if lang_name == target_display:
                        self.config.translation.target_language = lang_code
                        break

            # Atualizar display
            self._update_current_config_display()

            # Mostrar confirmação
            messagebox.showinfo("Configurações", "Configurações aplicadas com sucesso!\n\nAs novas configurações serão usadas na próxima transcrição.")

        except Exception as e:
            logger.error(f"Erro ao aplicar configurações: {e}")
            messagebox.showerror("Erro", f"Erro ao aplicar configurações:\n{e}")

    def _update_current_config_display(self):
        """Atualiza o display das configurações atuais."""
        try:
            model = getattr(self.config.transcription, 'model_name', 'unknown')
            device = getattr(self.config.audio, 'device_index', 'auto')
            lang = getattr(self.config.transcription, 'language', None) or 'auto'
            translate = getattr(self.config.translation, 'enabled', False)
            target_lang = getattr(self.config.translation, 'target_language', 'pt')
            use_vad = getattr(self.config.transcription, 'use_vad', False)
            vad_aggr = getattr(self.config.transcription, 'vad_aggressiveness', 2)

            lang_display = self.available_languages.get(lang, lang)
            target_display = self.available_languages.get(target_lang, target_lang)

            config_text = f"Atual: Modelo={model} | Dispositivo={device} | Idioma={lang_display}"

            if use_vad:
                config_text += f" | VAD=Ativo({vad_aggr})"
            else:
                config_text += " | VAD=Desabilitado"

            if translate:
                config_text += f" | Tradução→{target_display}"
            else:
                config_text += " | Tradução=Desabilitada"

            self.current_config_var.set(config_text)

        except Exception as e:
            logger.error(f"Erro ao atualizar display de configuração: {e}")
            self.current_config_var.set("Erro ao carregar configurações")

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

            # Adicionar ao texto principal
            self.transcriptions_text.insert(tk.END, entry)
            self.transcriptions_text.see(tk.END)  # Auto-scroll

            # Adicionar ao teleprompter com timestamp e tradução
            self.update_teleprompter(text, translation)

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
            last_text = None
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].startswith('[') and ']' in lines[i]:
                    # Extrair texto da transcrição para o teleprompter
                    line = lines[i]
                    if ') ' in line:
                        last_text = line.split(') ', 1)[1]

                    # Inserir tradução na interface principal
                    insert_pos = f"{i+2}.0"
                    self.transcriptions_text.insert(insert_pos, f"    → {translation}\n")
                    self.transcriptions_text.see(tk.END)
                    break

            # Atualizar teleprompter com tradução
            if last_text and self.teleprompter_text_widget:
                try:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Adicionar apenas a tradução ao teleprompter
                    teleprompter_entry = f"    → {translation}\n\n"
                    self.teleprompter_text_widget.insert(tk.END, teleprompter_entry)
                    self.teleprompter_text_widget.see(tk.END)
                except tk.TclError:
                    # Janela foi fechada
                    self.teleprompter_window = None
                    self.teleprompter_text_widget = None

            self.current_stats['translation_count'] += 1

        self.root.after(0, update_ui)

    def update_audio_level(self, level: float):
        """Atualiza nível de áudio."""
        self.current_stats['current_audio_level'] = level
        self._update_transcription_state(level)

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


class TeleprompterWindow:
    """Janela do teleprompter transparente."""

    def __init__(self, parent_interface):
        self.parent = parent_interface

        # Configurações do teleprompter
        self.font_size = 24
        self.font_family = "Arial"
        self.bg_color = "#000000"  # Preto
        self.text_color = "#FFFFFF"  # Branco
        self.transparency = 0.8  # 80% opaco
        self.border_width = 2
        self.border_color = "#FFFFFF"
        self.current_bg = self.bg_color  # Cor atual do fundo

        self._create_window()
        self._setup_ui()

        # Registrar no parent
        self.parent.teleprompter_text_widget = self.text_widget

    def _create_window(self):
        """Cria a janela principal do teleprompter com transparência controlada."""
        self.root = tk.Toplevel(self.parent.root)
        self.root.title("📺 Teleprompter - Whisper")
        self.root.geometry("800x600+100+100")

        # Manter decorações da janela para facilitar movimento
        self.root.overrideredirect(False)
        
        # Configurar atributos da janela
        self.root.wm_attributes("-topmost", True)
        
        # Aplicar transparência inicial de forma controlada
        self.root.wm_attributes("-alpha", 0.95)  # Ligeiramente transparente, mas controles visíveis
        
        # Configurar cor de fundo
        self.root.configure(bg=self.bg_color)
        
        # Configurar estrutura de transparência
        self._setup_transparent_background()

        # Configurar fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _setup_transparent_background(self):
        """Configura o fundo com transparência controlada."""
        # Container principal - sem transparência para manter controles visíveis
        self.main_container = tk.Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar cor inicial
        self.current_bg = self.bg_color

    def _update_transparency(self):
        """Atualiza a transparência da janela de forma controlada."""
        try:
            # Aplicar transparência à janela, mas manter um mínimo para visibilidade dos controles
            alpha_value = max(0.7, self.transparency)  # Mínimo de 70% para manter controles visíveis
            self.root.wm_attributes("-alpha", alpha_value)
            
            # Ajustar cor de fundo baseada na transparência para efeito visual
            if self.transparency < 0.6:
                # Alta transparência: fundo bem escuro
                self.current_bg = "#0a0a0a"
            elif self.transparency < 0.8:
                # Transparência média: fundo escuro
                self.current_bg = "#1a1a1a"  
            else:
                # Baixa transparência: usar cor configurada
                self.current_bg = self.bg_color
                
            # Atualizar componentes
            self._update_background_colors()
                
        except Exception as e:
            print(f"Erro ao aplicar transparência: {e}")
            # Fallback
            self.current_bg = self.bg_color
            self._update_background_colors()

    def _update_background_colors(self):
        """Atualiza cores de fundo dos componentes."""
        if hasattr(self, 'main_container'):
            self.main_container.configure(bg=self.current_bg)
        if hasattr(self, 'text_widget'):
            self.text_widget.configure(bg=self.current_bg, fg=self.text_color)

    def _setup_ui(self):
        """Configura a interface do teleprompter."""
        # Frame principal de conteúdo
        main_frame = tk.Frame(
            self.main_container,
            bg=self.current_bg,
            highlightbackground=self.border_color,
            highlightthickness=self.border_width
        )
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.main_frame = main_frame  # Guardar referência

        # Frame de controles (no topo)
        controls_frame = tk.Frame(main_frame, bg=self.current_bg)
        controls_frame.pack(fill="x", padx=5, pady=5)
        self.controls_frame = controls_frame  # Guardar referência

        # Título
        title_label = tk.Label(
            controls_frame,
            text="📺 Teleprompter",
            font=(self.font_family, 14, "bold"),
            bg=self.current_bg,
            fg=self.text_color
        )
        title_label.pack(side="left")

        # Controles de configuração
        config_frame = tk.Frame(controls_frame, bg=self.current_bg)
        config_frame.pack(side="right")
        self.config_frame = config_frame  # Guardar referência

        # Botão de transparência (bem visível)
        transparency_btn = tk.Button(
            config_frame, 
            text="👁️", 
            command=self._toggle_transparency,
            bg="#333333", 
            fg="white", 
            width=4,
            font=(self.font_family, 12, "bold")
        )
        transparency_btn.pack(side="left", padx=2)

        # Tamanho da fonte
        tk.Label(config_frame, text="Fonte:", bg=self.current_bg, fg=self.text_color).pack(side="left")

        font_down_btn = tk.Button(config_frame, text="A-", command=self._decrease_font, width=3)
        font_down_btn.pack(side="left", padx=2)

        font_up_btn = tk.Button(config_frame, text="A+", command=self._increase_font, width=3)
        font_up_btn.pack(side="left", padx=2)

        # Transparência
        tk.Label(config_frame, text="Opacidade:", bg=self.current_bg, fg=self.text_color).pack(side="left", padx=(10, 0))

        opacity_down_btn = tk.Button(config_frame, text="-", command=self._decrease_opacity, width=3)
        opacity_down_btn.pack(side="left", padx=2)

        opacity_up_btn = tk.Button(config_frame, text="+", command=self._increase_opacity, width=3)
        opacity_up_btn.pack(side="left", padx=2)

        # Cores
        color_btn = tk.Button(config_frame, text="🎨 Cores", command=self._change_colors)
        color_btn.pack(side="left", padx=(10, 0))

        # Limpar
        clear_btn = tk.Button(config_frame, text="🗑️", command=self._clear_text)
        clear_btn.pack(side="left", padx=2)

        # Alternar GUI principal
        toggle_gui_btn = tk.Button(config_frame, text="🔄 GUI", command=self.parent.toggle_gui_visibility)
        toggle_gui_btn.pack(side="left", padx=2)

        # Área de texto
        text_frame = tk.Frame(main_frame, bg=self.current_bg)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_frame = text_frame  # Guardar referência

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        # Widget de texto
        self.text_widget = tk.Text(
            text_frame,
            font=(self.font_family, self.font_size, "bold"),
            bg=self.current_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground="#444444",
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            borderwidth=0,
            highlightthickness=0
        )
        self.text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_widget.yview)

        # Vincular teclas
        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<Control-plus>", lambda e: self._increase_font())
        self.root.bind("<Control-minus>", lambda e: self._decrease_font())
        self.root.bind("<F2>", lambda e: self.parent.toggle_gui_visibility())  # F2 para alternar GUI

    def _increase_font(self):
        """Aumenta o tamanho da fonte."""
        if self.font_size < 72:
            self.font_size += 2
            self._update_font()

    def _decrease_font(self):
        """Diminui o tamanho da fonte."""
        if self.font_size > 12:
            self.font_size -= 2
            self._update_font()

    def _update_font(self):
        """Atualiza a fonte do texto."""
        self.text_widget.config(font=(self.font_family, self.font_size, "bold"))

    def _increase_opacity(self):
        """Aumenta a opacidade."""
        if self.transparency < 1.0:
            self.transparency += 0.1
            self._update_transparency()

    def _decrease_opacity(self):
        """Diminui a opacidade."""
        if self.transparency > 0.2:
            self.transparency -= 0.1
            self._update_transparency()

    def _toggle_transparency(self):
        """Alterna entre alta e baixa transparência rapidamente."""
        if self.transparency > 0.8:
            self.transparency = 0.5  # Mais transparente
        else:
            self.transparency = 0.9  # Menos transparente
        self._update_transparency()

    def _change_colors(self):
        """Abre diálogo para mudar cores."""
        from tkinter import colorchooser

        # Escolher cor do fundo
        bg_color = colorchooser.askcolor(
            title="Escolher cor de fundo",
            initialcolor=self.bg_color
        )

        if bg_color[1]:  # Se cor foi escolhida
            self.bg_color = bg_color[1]

            # Escolher cor do texto
            text_color = colorchooser.askcolor(
                title="Escolher cor do texto",
                initialcolor=self.text_color
            )

            if text_color[1]:
                self.text_color = text_color[1]

            # Aplicar cores
            self._apply_colors()

    def _apply_colors(self):
        """Aplica as cores selecionadas."""
        # Atualizar cor atual e aplicar transparência
        self._update_transparency()

        # Atualizar widget de texto
        if hasattr(self, 'text_widget'):
            self.text_widget.config(bg=self.current_bg, fg=self.text_color, insertbackground=self.text_color)

        # Atualizar containers e frames principais
        if hasattr(self, 'main_container'):
            self.main_container.configure(bg=self.current_bg)
        if hasattr(self, 'main_frame'):
            self.main_frame.configure(bg=self.current_bg)
        if hasattr(self, 'controls_frame'):
            self.controls_frame.configure(bg=self.current_bg)
        if hasattr(self, 'config_frame'):
            self.config_frame.configure(bg=self.current_bg)
        if hasattr(self, 'text_frame'):
            self.text_frame.configure(bg=self.current_bg)

        # Atualizar labels recursivamente
        self._update_widget_colors(self.root)

    def _update_widget_colors(self, widget):
        """Atualiza cores de widgets recursivamente."""
        try:
            if isinstance(widget, tk.Label):
                widget.configure(bg=self.current_bg, fg=self.text_color)
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=self.current_bg)

            # Atualizar filhos
            for child in widget.winfo_children():
                self._update_widget_colors(child)
        except:
            pass

    def _clear_text(self):
        """Limpa o texto do teleprompter."""
        self.text_widget.delete(1.0, tk.END)

    def close(self):
        """Fecha a janela do teleprompter."""
        self.parent.close_teleprompter()

    def destroy(self):
        """Destrói a janela."""
        self.root.destroy()
