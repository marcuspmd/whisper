"""
Interface interativa com rich para visualização em tempo real.
"""
import threading
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionEntry:
    """Entrada de transcrição com metadados."""
    timestamp: datetime
    text: str
    language: str
    confidence: float = 0.0
    translation: Optional[str] = None

@dataclass
class AppStats:
    """Estatísticas da aplicação."""
    start_time: datetime = field(default_factory=datetime.now)
    total_transcriptions: int = 0
    languages_detected: Dict[str, int] = field(default_factory=dict)
    translation_count: int = 0
    average_confidence: float = 0.0
    current_audio_level: float = 0.0
    processing_time_avg: float = 0.0

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich.live import Live
    from rich import box
    RICH_AVAILABLE = True

    class InteractiveConsole:
        """Console interativo com rich para visualização em tempo real."""

        def __init__(self, config):
            self.config = config
            self.stats = AppStats()
            self.recent_transcriptions: List[TranscriptionEntry] = []
            self.max_recent = 10

            # Estado da aplicação
            self.running = False
            self.live_display = None
            self.update_thread = None
            self.lock = threading.Lock()

            # Console rich
            self.console = Console()
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            )
            self.setup_layout()

        def setup_layout(self):
            """Configura o layout da interface."""
            self.layout = Layout()

            # Divisão principal
            self.layout.split(
                Layout(name="header", size=3),
                Layout(name="main", ratio=1),
                Layout(name="footer", size=3),
            )

            # Divisão do main
            self.layout["main"].split_row(
                Layout(name="left", ratio=2),
                Layout(name="right", ratio=1),
            )

            # Divisão do lado esquerdo
            self.layout["left"].split(
                Layout(name="transcriptions", ratio=2),
                Layout(name="audio_status", size=8),
            )

            # Divisão do lado direito
            self.layout["right"].split(
                Layout(name="config", ratio=1),
                Layout(name="stats", ratio=1),
            )

        def start(self):
            """Inicia a interface interativa."""
            self.running = True

            # Thread para atualização da interface
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()

            # Display ao vivo
            self.live_display = Live(
                self.layout,
                console=self.console,
                screen=True,
                redirect_stderr=True,
                redirect_stdout=True
            )

            try:
                with self.live_display:
                    # Não imprimir nada durante o Live display para evitar flickers
                    while self.running:
                        time.sleep(0.1)

            except KeyboardInterrupt:
                self.running = False

        def stop(self):
            """Para a interface."""
            self.running = False
            if self.update_thread:
                self.update_thread.join(timeout=1.0)

        def add_transcription(self, text: str, language: str, confidence: float = 0.0, translation: str = None):
            """Adiciona nova transcrição."""
            with self.lock:
                entry = TranscriptionEntry(
                    timestamp=datetime.now(),
                    text=text,
                    language=language,
                    confidence=confidence,
                    translation=translation
                )

                self.recent_transcriptions.append(entry)
                if len(self.recent_transcriptions) > self.max_recent:
                    self.recent_transcriptions.pop(0)

                # Atualiza estatísticas
                self.stats.total_transcriptions += 1
                if language in self.stats.languages_detected:
                    self.stats.languages_detected[language] += 1
                else:
                    self.stats.languages_detected[language] = 1

                if translation:
                    self.stats.translation_count += 1

                # Atualiza confiança média
                if confidence > 0:
                    total_confidence = (self.stats.average_confidence * (self.stats.total_transcriptions - 1) + confidence)
                    self.stats.average_confidence = total_confidence / self.stats.total_transcriptions

        def update_audio_level(self, level: float):
            """Atualiza nível de áudio atual."""
            with self.lock:
                self.stats.current_audio_level = level

        def update_last_translation(self, translation: str):
            """Atualiza a tradução da última transcrição."""
            with self.lock:
                if self.recent_transcriptions:
                    self.recent_transcriptions[-1].translation = translation
                    self.stats.translation_count += 1

        def set_audio_device(self, device_name: str):
            """Define o nome do dispositivo de áudio ativo."""
            # Pode ser usado para mostrar na interface se necessário
            pass

        def show_status(self, message: str):
            """Mostra mensagem de status."""
            pass

        def _update_loop(self):
            """Loop de atualização da interface."""
            while self.running:
                try:
                    self._update_display()
                    time.sleep(0.5)  # Atualiza 2x por segundo
                except Exception as e:
                    logger.error(f"Erro na atualização da interface: {e}")

        def _update_display(self):
            """Atualiza o display da interface."""
            if not self.layout:
                return

            # Header
            uptime = datetime.now() - self.stats.start_time
            header_text = Text.assemble(
                ("🎙️ Whisper Transcriber", "bold green"),
                f" • Ativo há {str(uptime).split('.')[0]}"
            )
            self.layout["header"].update(
                Panel(Align.center(header_text), box=box.ROUNDED)
            )

            # Transcrições recentes
            self.layout["transcriptions"].update(self._render_transcriptions())

            # Status de áudio
            self.layout["audio_status"].update(self._render_audio_status())

            # Configurações
            self.layout["config"].update(self._render_config())

            # Estatísticas
            self.layout["stats"].update(self._render_stats())

            # Footer
            footer_text = Text.assemble(
                ("Ctrl+C", "bold red"),
                " para sair • ",
                ("Transcrições: ", ""),
                (str(self.stats.total_transcriptions), "bold cyan")
            )
            self.layout["footer"].update(
                Panel(Align.center(footer_text), box=box.ROUNDED)
            )

        def _render_transcriptions(self) -> Panel:
            """Renderiza painel de transcrições."""
            if not self.recent_transcriptions:
                content = "[dim]Aguardando transcrições...[/dim]"
            else:
                lines = []
                for entry in reversed(self.recent_transcriptions[-5:]):  # Últimas 5
                    time_str = entry.timestamp.strftime("%H:%M:%S")
                    lang_flag = self._get_language_flag(entry.language)

                    # Linha principal
                    confidence_color = "green" if entry.confidence > 0.8 else "yellow" if entry.confidence > 0.5 else "red"
                    confidence_str = f"({entry.confidence:.1f})" if entry.confidence > 0 else ""

                    line = Text.assemble(
                        (f"[{time_str}] ", "dim"),
                        (lang_flag, ""),
                        (f" {entry.text}", "white"),
                        (f" {confidence_str}", confidence_color)
                    )
                    lines.append(line)

                    # Tradução se disponível
                    if entry.translation:
                        translation_line = Text.assemble(
                            ("         ", ""),
                            ("🔄 ", "blue"),
                            (entry.translation, "cyan")
                        )
                        lines.append(translation_line)

                    lines.append(Text(""))  # Linha vazia

                content = "\n".join(str(line) for line in lines)

            return Panel(
                content,
                title="📝 Transcrições Recentes",
                border_style="blue",
                box=box.ROUNDED
            )

        def _render_audio_status(self) -> Panel:
            """Renderiza status de áudio."""
            # Barra de nível de áudio
            level = self.stats.current_audio_level
            bar_width = 30
            filled = int(level * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            # Cor baseada no nível
            if level > 0.7:
                color = "red"
            elif level > 0.3:
                color = "yellow"
            else:
                color = "green"

            content = Text.assemble(
                ("Nível: ", "white"),
                (f"[{bar}]", color),
                (f" {level:.1%}", "white"),
                ("\n\n", ""),
                ("Status: ", "white"),
                ("🟢 Ativo" if self.running else "🔴 Parado", "green" if self.running else "red")
            )

            return Panel(
                content,
                title="🔊 Status de Áudio",
                border_style="green",
                box=box.ROUNDED
            )

        def _render_config(self) -> Panel:
            """Renderiza configurações ativas."""
            audio_cfg = self.config.audio
            trans_cfg = self.config.transcription

            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Setting", style="dim")
            table.add_column("Value", style="white")

            table.add_row("Modelo:", trans_cfg.model_name)
            table.add_row("Dispositivo:", f"ID {audio_cfg.device_id}")
            table.add_row("Taxa:", f"{audio_cfg.sample_rate}Hz")
            table.add_row("Chunk:", f"{audio_cfg.chunk_seconds}s")

            if hasattr(trans_cfg, 'language') and trans_cfg.language:
                table.add_row("Idioma:", trans_cfg.language)

            return Panel(
                table,
                title="⚙️ Configurações",
                border_style="yellow",
                box=box.ROUNDED
            )

        def _render_stats(self) -> Panel:
            """Renderiza estatísticas."""
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Stat", style="dim")
            table.add_column("Value", style="cyan")

            # Estatísticas básicas
            table.add_row("Total:", str(self.stats.total_transcriptions))
            table.add_row("Traduções:", str(self.stats.translation_count))

            if self.stats.average_confidence > 0:
                table.add_row("Confiança:", f"{self.stats.average_confidence:.1%}")

            # Idiomas mais detectados
            if self.stats.languages_detected:
                top_lang = max(self.stats.languages_detected.items(), key=lambda x: x[1])
                flag = self._get_language_flag(top_lang[0])
                table.add_row("Top idioma:", f"{flag} {top_lang[1]}x")

            return Panel(
                table,
                title="📊 Estatísticas",
                border_style="magenta",
                box=box.ROUNDED
            )

        def _get_language_flag(self, lang_code: str) -> str:
            """Retorna emoji da bandeira para o idioma."""
            flags = {
                'pt': '🇧🇷', 'en': '🇺🇸', 'es': '🇪🇸', 'fr': '🇫🇷',
                'de': '🇩🇪', 'it': '🇮🇹', 'ja': '🇯🇵', 'ko': '🇰🇷',
                'zh': '🇨🇳', 'ru': '🇷🇺', 'ar': '🇸🇦', 'hi': '🇮🇳',
                'nl': '🇳🇱', 'sv': '🇸🇪', 'no': '🇳🇴', 'da': '🇩🇰',
                'fi': '🇫🇮', 'pl': '🇵🇱', 'tr': '🇹🇷', 'bg': '🇧🇬',
                'nn': '🇳🇴'
            }
            return flags.get(lang_code, '🌐')

except ImportError:
    RICH_AVAILABLE = False

    class InteractiveConsole:
        """Fallback para quando rich não está disponível."""
        def __init__(self, config):
            from .simple import SimpleConsole
            self.console = SimpleConsole(config)

        def start(self):
            return self.console.start()
        def stop(self):
            return self.console.stop()
        def add_transcription(self, text: str, language: str, confidence: float = 0.0, translation: str = None):
            return self.console.add_transcription(text, language, confidence, translation)
        def update_audio_level(self, level: float):
            return self.console.update_audio_level(level)
        def update_last_translation(self, translation: str):
            return self.console.update_last_translation(translation) if hasattr(self.console, 'update_last_translation') else None
        def set_audio_device(self, device_name: str):
            return self.console.set_audio_device(device_name) if hasattr(self.console, 'set_audio_device') else None
        def show_status(self, message: str):
            return self.console.show_status(message)
