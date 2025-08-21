#!/usr/bin/env python3
"""
Teste para verificar dispositivos de áudio disponíveis
"""
import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.audio.device_manager import AudioDeviceManager

    print("🎤 Testando carregamento de dispositivos de áudio...")

    device_manager = AudioDeviceManager()
    devices = device_manager.get_input_devices()

    print(f"\n✅ Encontrados {len(devices)} dispositivos de entrada:")
    for device_id, device_name in devices:
        print(f"  - ID {device_id}: {device_name}")

except Exception as e:
    print(f"❌ Erro ao carregar dispositivos: {e}")
    import traceback
    traceback.print_exc()
