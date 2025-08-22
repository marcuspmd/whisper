#!/usr/bin/env python3
"""
Teste para verificar seleção de dispositivos de áudio
"""
import sys
from pathlib import Path

# Adiciona src ao path para imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.config.settings import get_config_manager
from src.audio.device_manager import AudioDeviceManager

def test_device_selection():
    """Testa seleção de dispositivos"""

    # Carrega configuração
    config_manager = get_config_manager()
    config = config_manager.config

    print("=== Teste de Seleção de Dispositivos ===")
    print(f"Device ID configurado: {config.audio.device_id}")
    print(f"Device Name configurado: {config.audio.device_name}")

    # Lista dispositivos disponíveis
    device_manager = AudioDeviceManager()
    devices = device_manager.get_input_devices()

    print("\n=== Dispositivos Disponíveis ===")
    for device_id, device_name in devices:
        marker = " <<< SELECIONADO" if device_id == config.audio.device_id else ""
        print(f"ID {device_id}: {device_name}{marker}")

    # Verifica se o dispositivo configurado existe
    configured_device = None
    for device_id, device_name in devices:
        if device_id == config.audio.device_id:
            configured_device = device_name
            break

    if configured_device:
        print(f"\n✅ Dispositivo configurado encontrado: {configured_device}")

        # Testa se consegue criar AudioCapture com esse dispositivo
        try:
            from src.audio.capture import AudioCapture
            capture = AudioCapture(
                device_index=config.audio.device_id,
                sample_rate=config.audio.sample_rate,
                channels=config.audio.channels,
                buffer_seconds=5  # Buffer menor para teste
            )
            print("✅ AudioCapture criado com sucesso")

            # Inicia captura
            if capture.start():
                print("✅ Captura de áudio iniciada")

                # Aguarda um pouco para capturar dados
                import time
                time.sleep(2)

                # Verifica se há dados no buffer
                buffer_duration = capture.buffer.get_buffer_duration()
                print(f"✅ Buffer contém {buffer_duration:.2f} segundos de áudio")

                if buffer_duration > 0:
                    print("✅ Dispositivo está capturando áudio corretamente")
                else:
                    print("❌ Dispositivo não está capturando áudio")

                capture.stop()
            else:
                print("❌ Falha ao iniciar captura de áudio")

        except Exception as e:
            print(f"❌ Erro ao testar captura de áudio: {e}")
            import traceback
            traceback.print_exc()

    else:
        print(f"\n❌ Dispositivo configurado (ID {config.audio.device_id}) não encontrado!")

    print("\n=== Teste Concluído ===")

if __name__ == "__main__":
    test_device_selection()
