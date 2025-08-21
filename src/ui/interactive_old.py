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
                redirect_stderr=False
            )
            
            try:
                with self.live_display:
                    self.console.print("🎙️ [bold green]Whisper Transcriber Interativo[/bold green]")
                    self.console.print("Pressione [bold red]Ctrl+C[/bold red] para sair\n")
                    
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
            
            table.add_row("Modelo:", trans_cfg.model_size)
            table.add_row("Dispositivo:", f"ID {audio_cfg.input_device_id}")
            table.add_row("Taxa:", f"{audio_cfg.sample_rate}Hz")
            table.add_row("Chunk:", f"{audio_cfg.chunk_size}")
            
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
        def show_status(self, message: str):
            return self.console.show_status(message)
    
    def setup_layout(self):
        """Configura o layout da interface."""
        if not RICH_AVAILABLE:
            return
            
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
        if not RICH_AVAILABLE:
            return self.console.start()
            
        self.running = True
        
        # Thread para atualização da interface
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        # Display ao vivo
        self.live_display = Live(
            self.layout, 
            console=self.console, 
            screen=True, 
            redirect_stderr=False
        )
        
        try:
            with self.live_display:
                self.console.print("🎙️ [bold green]Whisper Transcriber Interativo[/bold green]")
                self.console.print("Pressione [bold red]Ctrl+C[/bold red] para sair\n")
                
                while self.running:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            self.running = False
            
    def stop(self):
        """Para a interface."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
            
        if not RICH_AVAILABLE:
            return self.console.stop()
            
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
                
        if not RICH_AVAILABLE:
            self.console.add_transcription(text, language, confidence, translation)
            
    def update_audio_level(self, level: float):
        """Atualiza nível de áudio atual."""
        with self.lock:
            self.stats.current_audio_level = level
            
        if not RICH_AVAILABLE:
            self.console.update_audio_level(level)
            
    def show_status(self, message: str):
        """Mostra mensagem de status."""
        if not RICH_AVAILABLE:
            self.console.show_status(message)
            
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
        if not RICH_AVAILABLE or not self.layout:
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
            ("\n", ""),
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
        
        table.add_row("Modelo:", trans_cfg.model_size)
        table.add_row("Dispositivo:", f"ID {audio_cfg.input_device_id}")
        table.add_row("Taxa:", f"{audio_cfg.sample_rate}Hz")
        table.add_row("Chunk:", f"{audio_cfg.chunk_size}")
        
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
    
    def get_table(self) -> Table:
        """Retorna tabela formatada com transcrições"""
        table = Table(
            title="📝 Transcrições Recentes",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Horário", style="dim", width=8)
        table.add_column("Idioma", style="blue", width=6)
        table.add_column("Original", style="white", min_width=20)
        table.add_column("Tradução", style="green", min_width=20)
        
        for item in list(self.items)[-10:]:  # Últimos 10 itens
            timestamp_str = item['timestamp'].strftime("%H:%M:%S")
            original = item['original'][:50] + "..." if len(item['original']) > 50 else item['original']
            translated = item['translated'][:50] + "..." if item['translated'] and len(item['translated']) > 50 else (item['translated'] or "-")
            
            table.add_row(
                timestamp_str,
                item['language'].upper(),
                original,
                translated
            )
        
        return table
    
    def get_stats_table(self) -> Table:
        """Retorna tabela com estatísticas"""
        table = Table(
            title="📊 Estatísticas da Sessão",
            box=box.ROUNDED,
            show_header=False
        )
        
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="white")
        
        session_duration = datetime.now() - self.stats['session_start']
        hours, remainder = divmod(int(session_duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        table.add_row("⏱️ Tempo de sessão", f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        table.add_row("📝 Total de transcrições", str(self.stats['total_transcriptions']))
        table.add_row("💬 Total de palavras", str(self.stats['total_words']))
        
        if self.stats['last_activity']:
            last_activity = (datetime.now() - self.stats['last_activity']).total_seconds()
            table.add_row("🕐 Última atividade", f"{int(last_activity)}s atrás")
        
        return table


class AudioLevelDisplay:
    """Display para nível de áudio"""
    
    def __init__(self):
        self.current_level = 0.0
        self.peak_level = 0.0
        self.is_silent = True
        self.device_name = "Dispositivo padrão"
    
    def update_level(self, level: float, is_silent: bool = False):
        """Atualiza nível de áudio"""
        self.current_level = level
        self.is_silent = is_silent
        
        if level > self.peak_level:
            self.peak_level = level
    
    def set_device_name(self, name: str):
        """Define nome do dispositivo"""
        self.device_name = name
    
    def get_panel(self) -> Panel:
        """Retorna panel com visualização de áudio"""
        # Barra de nível
        bar_width = 40
        filled = int((self.current_level / 100.0) * bar_width)
        
        bar = "█" * filled + "░" * (bar_width - filled)
        
        status_emoji = "🔇" if self.is_silent else "🎤"
        status_text = "Silêncio" if self.is_silent else "Detectando áudio"
        
        content = f"""
{status_emoji} {status_text}

Dispositivo: {self.device_name}
Nível atual: {self.current_level:.1f} RMS
Pico: {self.peak_level:.1f} RMS

[{bar}]
"""
        
        return Panel(
            content,
            title="🎵 Monitor de Áudio",
            border_style="green" if not self.is_silent else "dim"
        )


class ConfigurationDisplay:
    """Display para configurações"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
    
    def get_table(self) -> Table:
        """Retorna tabela com configurações atuais"""
        config = self.config_manager.config
        
        table = Table(
            title="⚙️ Configurações Atuais",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold yellow"
        )
        
        table.add_column("Categoria", style="cyan", width=12)
        table.add_column("Configuração", style="white", width=20)
        table.add_column("Valor", style="green", width=20)
        
        # Configurações de áudio
        table.add_row("🎵 Áudio", "Taxa de amostragem", f"{config.audio.sample_rate} Hz")
        table.add_row("", "Dispositivo", config.audio.device_name or f"ID: {config.audio.device_id}" if config.audio.device_id else "Padrão")
        table.add_row("", "Chunk", f"{config.audio.chunk_seconds}s")
        
        # Configurações de transcrição
        table.add_row("🤖 Transcrição", "Modelo", config.transcription.model_name)
        table.add_row("", "Dispositivo", config.transcription.device)
        table.add_row("", "Idioma", config.transcription.language or "Auto-detect")
        table.add_row("", "VAD", "✅" if config.transcription.use_vad else "❌")
        
        # Configurações de tradução
        table.add_row("🌐 Tradução", "Ativo", "✅" if config.translation.enabled else "❌")
        table.add_row("", "Modo", config.translation.mode.title())
        table.add_row("", "Idioma de destino", config.translation.target_language.upper())
        
        return table


class InteractiveConsole:
    """Console interativo principal"""
    
    def __init__(self):
        self.console = Console()
        self.config_manager = get_config_manager()
        
        # Displays
        self.transcription_display = TranscriptionDisplay()
        self.audio_display = AudioLevelDisplay()
        self.config_display = ConfigurationDisplay(self.config_manager)
        
        # Estado
        self.is_running = False
        self.live = None
        self.refresh_rate = 10  # Hz
        
        # Callbacks
        self.on_transcription_callback: Optional[Callable] = None
        self.on_config_change_callback: Optional[Callable] = None
    
    def set_transcription_callback(self, callback: Callable):
        """Define callback para novas transcrições"""
        self.on_transcription_callback = callback
    
    def set_config_change_callback(self, callback: Callable):
        """Define callback para mudanças de configuração"""
        self.on_config_change_callback = callback
    
    def add_transcription(self, original: str, translated: Optional[str] = None, language: Optional[str] = None):
        """Adiciona nova transcrição ao display"""
        self.transcription_display.add_transcription(original, translated, language)
    
    def update_audio_level(self, level: float, is_silent: bool = False):
        """Atualiza nível de áudio"""
        self.audio_display.update_level(level, is_silent)
    
    def set_audio_device(self, device_name: str):
        """Define dispositivo de áudio"""
        self.audio_display.set_device_name(device_name)
    
    def create_layout(self) -> Layout:
        """Cria layout da interface"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right", ratio=2)
        )
        
        layout["left"].split_column(
            Layout(name="audio", size=12),
            Layout(name="config")
        )
        
        layout["right"].split_column(
            Layout(name="transcriptions", ratio=2),
            Layout(name="stats", size=8)
        )
        
        return layout
    
    def update_layout(self, layout: Layout):
        """Atualiza conteúdo do layout"""
        # Header
        header_text = Text("🎙️ Whisper Real-time Transcriber", style="bold cyan")
        layout["header"].update(Align.center(Panel(header_text, box=box.HEAVY)))
        
        # Áudio
        layout["audio"].update(self.audio_display.get_panel())
        
        # Configurações
        layout["config"].update(self.config_display.get_table())
        
        # Transcrições
        layout["transcriptions"].update(self.transcription_display.get_table())
        
        # Estatísticas
        layout["stats"].update(self.transcription_display.get_stats_table())
        
        # Footer
        footer_text = Text("Pressione Ctrl+C para sair | F1: Ajuda | F2: Configurações", style="dim")
        layout["footer"].update(Align.center(Panel(footer_text, box=box.SIMPLE)))
    
    def show_welcome(self):
        """Mostra tela de boas-vindas"""
        welcome_panel = Panel(
            """
🎙️ [bold cyan]Whisper Real-time Transcriber v2.0[/bold cyan]

Transcrição e tradução em tempo real com interface interativa.

🎵 Monitor de áudio em tempo real
📝 Histórico de transcrições
🌐 Tradução automática
⚙️ Configurações persistentes

[dim]Pressione qualquer tecla para continuar...[/dim]
            """,
            title="Bem-vindo",
            border_style="cyan"
        )
        
        self.console.print(Align.center(welcome_panel))
        input()  # Aguarda tecla
        self.console.clear()
    
    def start(self):
        """Inicia interface interativa"""
        if self.is_running:
            return
        
        self.show_welcome()
        
        self.is_running = True
        layout = self.create_layout()
        
        try:
            with Live(
                layout,
                console=self.console,
                screen=True,
                refresh_per_second=self.refresh_rate
            ) as live:
                self.live = live
                
                while self.is_running:
                    self.update_layout(layout)
                    time.sleep(1.0 / self.refresh_rate)
                    
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Erro na interface: {e}")
            self.stop()
    
    def stop(self):
        """Para interface"""
        self.is_running = False
        if self.live:
            self.live.stop()
        
        self.console.print("\n[yellow]Interface finalizada.[/yellow]")
    
    def run_in_thread(self) -> threading.Thread:
        """Executa interface em thread separada"""
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
        return thread


def create_interactive_console() -> InteractiveConsole:
    """Factory function para criar console interativo"""
    return InteractiveConsole()
