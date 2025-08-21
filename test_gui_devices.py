#!/usr/bin/env python3
"""
Teste detalhado dos dispositivos detectados pela interface GUI
"""
import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.audio.device_manager import AudioDeviceManager

    print("🎤 Testando detecção de dispositivos pela GUI...")
    print("=" * 60)

    device_manager = AudioDeviceManager()
    devices = device_manager.get_input_devices()

    print(f"📋 Total de dispositivos detectados: {len(devices)}")
    print()

    for device_id, device_name in devices:
        # Aplicar a mesma lógica da GUI para categorização
        device_info = f"{device_id}: {device_name}"

        # Identificar tipos especiais (mesma lógica da GUI)
        name_lower = device_name.lower()
        category = "🎤 Dispositivo padrão"

        if any(keyword in name_lower for keyword in ['blackhole', 'loopback', 'soundflower', 'vb-audio', 'voicemeeter']):
            device_info += " [Virtual Audio]"
            category = "🔧 Virtual Audio Driver"
        elif any(keyword in name_lower for keyword in ['aggregate', 'agregado', 'combined', 'conjunto']):
            device_info += " [Dispositivo Agregado]"
            category = "🎯 Dispositivo Agregado macOS"
        elif any(keyword in name_lower for keyword in ['múltipla', 'multiple', 'multi-output', 'multi output']):
            device_info += " [Multi-Output Virtual]"
            category = "🔧 Multi-Output Virtual Device"
        elif any(keyword in name_lower for keyword in ['obs', 'audio hijack', 'rogue amoeba', 'studio', 'interface']):
            device_info += " [Software Audio]"
            category = "🎛️ Software Audio Tool"
        elif 'macbook' in name_lower or 'built-in' in name_lower:
            device_info += " [Interno]"
            category = "💻 Microfone interno"
        elif any(keyword in name_lower for keyword in ['usb', 'wireless', 'bluetooth']):
            device_info += " [Externo]"
            category = "🔌 Dispositivo externo"

        print(f"  {category}")
        print(f"    → {device_info}")
        print()

    print("✅ Todos estes dispositivos aparecerão no dropdown da GUI!")

except Exception as e:
    print(f"❌ Erro ao carregar dispositivos: {e}")
    import traceback
    traceback.print_exc()
