#!/usr/bin/env python3
"""
Whisper Real-time Transcriber v2.0
Transcrição e tradução de áudio em tempo real com interface interativa
"""
import argparse
import sys
import multiprocessing as mp
from pathlib import Path

# Configura multiprocessing para evitar problemas no macOS com interfaces gráficas
if sys.platform == "darwin":  # macOS
    mp.set_start_method("fork", force=True)

# Adiciona src ao path para imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.app import create_app
from src.audio.device_manager import AudioDeviceManager
from src.config.settings import get_config_manager
from src.utils.logger import setup_colored_logging


def create_parser() -> argparse.ArgumentParser:
    """Cria parser de argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description="Whisper Real-time Transcriber v2.0 - Transcrição e tradução em tempo real",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                                    # Modo GUI (padrão)
  python main.py --list-devices                     # Lista dispositivos de áudio
  python main.py --model small --language pt        # Modelo small, força português
  python main.py --console --no-translate           # Força modo console sem tradução
  python main.py --device-id 2 --translate-mode google  # Dispositivo específico, Google Translate
        """,
    )

    # Dispositivos de áudio
    audio_group = parser.add_argument_group("Configurações de Áudio")
    audio_group.add_argument(
        "--list-devices",
        action="store_true",
        help="Lista todos os dispositivos de áudio disponíveis e sai",
    )
    audio_group.add_argument(
        "--device-id",
        type=int,
        metavar="ID",
        help="ID do dispositivo de entrada (use --list-devices para ver os IDs)",
    )
    audio_group.add_argument(
        "--device-name",
        metavar="NOME",
        help="Substring do nome do dispositivo de entrada (ex: BlackHole)",
    )
    audio_group.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        metavar="RATE",
        help="Taxa de amostragem (default: 16000)",
    )
    audio_group.add_argument(
        "--chunk-seconds",
        type=int,
        default=3,
        metavar="SEC",
        help="Intervalo de processamento em segundos (default: 3)",
    )

    # Transcrição
    transcription_group = parser.add_argument_group("Configurações de Transcrição")
    transcription_group.add_argument(
        "--model",
        default="base",
        metavar="MODEL",
        help="Modelo Whisper (tiny, base, small, medium, large)",
    )
    transcription_group.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Dispositivo para processamento (cpu/cuda)",
    )
    transcription_group.add_argument(
        "--language",
        metavar="LANG",
        help="Idioma do áudio (pt, en, es, fr, etc.) - auto-detecta se não especificado",
    )
    transcription_group.add_argument(
        "--use-vad",
        action="store_true",
        help="Usar detecção de atividade de voz (requer webrtcvad)",
    )
    transcription_group.add_argument(
        "--vad-aggressiveness",
        type=int,
        default=2,
        choices=[0, 1, 2, 3],
        help="Agressividade do VAD (0-3, default: 2)",
    )

    # Tradução
    translation_group = parser.add_argument_group("Configurações de Tradução")
    translation_group.add_argument(
        "--no-translate",
        action="store_true",
        help="Desabilita tradução (apenas transcrição)",
    )
    translation_group.add_argument(
        "--translate-mode",
        default="local",
        choices=["local", "google"],
        help="Modo de tradução (default: local)",
    )
    translation_group.add_argument(
        "--target-language",
        default="pt",
        metavar="LANG",
        help="Idioma de destino para tradução (default: pt)",
    )

    # Interface
    ui_group = parser.add_argument_group("Configurações de Interface")
    ui_group.add_argument(
        "--console",
        action="store_true",
        help="Força modo console (fallback sem GUI)",
    )
    ui_group.add_argument(
        "--gui",
        action="store_true",
        help="Inicia interface desktop (aplicativo com janela) - PADRÃO",
    )
    ui_group.add_argument(
        "--teleprompter",
        action="store_true",
        help="Modo teleprompter (janela transparente para streaming)",
    )
    ui_group.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de log (default: INFO)",
    )
    ui_group.add_argument(
        "--no-color", action="store_true", help="Desabilita cores nos logs"
    )

    # Configuração
    config_group = parser.add_argument_group("Gerenciamento de Configuração")
    config_group.add_argument(
        "--save-config",
        action="store_true",
        help="Salva configurações atuais como padrão",
    )
    config_group.add_argument(
        "--reset-config",
        action="store_true",
        help="Reseta configurações para padrões de fábrica",
    )

    return parser


def apply_cli_args_to_config(args, config_manager):
    """Aplica argumentos da linha de comando à configuração"""
    config = config_manager.config

    # Áudio
    if args.device_id is not None:
        config.audio.device_id = args.device_id
    if args.device_name:
        config.audio.device_name = args.device_name
    if args.sample_rate:
        config.audio.sample_rate = args.sample_rate
    if args.chunk_seconds:
        config.audio.chunk_seconds = args.chunk_seconds

    # Transcrição
    if args.model:
        config.transcription.model_name = args.model
    if args.device:
        config.transcription.device = args.device
    if args.language:
        config.transcription.language = args.language
    if args.use_vad:
        config.transcription.use_vad = True
    if args.vad_aggressiveness:
        config.transcription.vad_aggressiveness = args.vad_aggressiveness

    # Tradução
    if args.no_translate:
        config.translation.enabled = False
    if args.translate_mode:
        config.translation.mode = args.translate_mode
    if args.target_language:
        config.translation.target_language = args.target_language

    # Interface - removido args.simple (não existe mais)
    if args.log_level:
        config.ui.log_level = args.log_level
    if args.no_color:
        config.ui.colored_logs = False


def main():
    """Função principal"""
    parser = create_parser()
    args = parser.parse_args()

    # Setup inicial de logging
    setup_colored_logging("INFO")

    # Lista dispositivos se solicitado
    if args.list_devices:
        device_manager = AudioDeviceManager()
        device_manager.print_devices()
        return 0

    # Gerenciador de configuração
    config_manager = get_config_manager()

    # Reset de configuração se solicitado
    if args.reset_config:
        import shutil

        if config_manager.config_file.exists():
            shutil.move(
                str(config_manager.config_file),
                str(config_manager.config_file.with_suffix(".bak")),
            )
        print("✅ Configurações resetadas para padrões de fábrica")
        config_manager = get_config_manager()  # Recarrega configurações padrão

    # Aplica argumentos da linha de comando
    apply_cli_args_to_config(args, config_manager)

    # Salva configuração se solicitado
    if args.save_config:
        config_manager.save()
        print("✅ Configurações salvas como padrão")
        return 0

    # Cria e executa aplicação
    try:
        # Verifica modo de interface
        if args.gui:
            # Modo interface desktop
            import threading

            from src.ui.desktop import DesktopInterface

            print("🖥️ Iniciando interface desktop...")

            # Cria aplicação em modo headless (sem interface terminal)
            app = create_app(use_simple_ui=True, headless=True)

            # Cria interface desktop
            desktop_interface = DesktopInterface(config_manager.config, config_manager=config_manager)

            # Conecta interface desktop à aplicação
            app.set_desktop_interface(desktop_interface)
            desktop_interface.set_app(app)

            # Executa interface desktop (bloqueia até janela fechar)
            desktop_interface.run()

        elif args.teleprompter:
            # Modo teleprompter
            print("📺 Iniciando modo teleprompter...")
            from src.ui.desktop import DesktopInterface

            # Cria aplicação em modo desktop com teleprompter
            app = create_app(use_simple_ui=False, headless=False)

            # Cria interface desktop em modo teleprompter
            desktop_interface = DesktopInterface(
                config_manager.config,
                teleprompter_mode=True
            )

            # Conecta interface à aplicação
            app.set_ui_interface(desktop_interface)

            # Inicia aplicação
            try:
                app.run()
            except KeyboardInterrupt:
                print("\n👋 Interrupção recebida, finalizando...")
            except Exception as e:
                print(f"\n❌ Erro: {e}")
        elif args.console:
            # Modo console forçado (fallback)
            print("🖥️ Executando em modo console...")
            app = create_app(use_simple_ui=True, headless=False)

            # Executa aplicação
            success = app.run()
            return 0 if success else 1
        else:
            # Modo padrão: tenta GUI primeiro, console como fallback
            try:
                print("🖥️ Iniciando interface desktop...")

                import threading
                from src.ui.desktop import DesktopInterface

                # Cria aplicação em modo headless (sem interface terminal)
                app = create_app(use_simple_ui=True, headless=True)

                # Cria interface desktop
                desktop_interface = DesktopInterface(config_manager.config)

                # Conecta interface desktop à aplicação
                app.set_desktop_interface(desktop_interface)
                desktop_interface.set_app(app)

                # Executa interface desktop (bloqueia até janela fechar)
                desktop_interface.run()

            except Exception as e:
                print(f"⚠️ Não foi possível iniciar GUI: {e}")
                print("🖥️ Executando em modo console fallback...")

                app = create_app(use_simple_ui=True, headless=False)
                success = app.run()
                return 0 if success else 1

    except KeyboardInterrupt:
        print("\n👋 Até logo!")
        return 0
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
