#!/usr/bin/env python3
"""
Instruções para criar um Dispositivo Agregado no macOS
"""

print("🔧 Como criar um Dispositivo Agregado no macOS:")
print("=" * 60)
print()
print("1. Abra o **Audio MIDI Setup** (Utilitários > Configuração MIDI Áudio)")
print("2. Clique no botão '+' no canto inferior esquerdo")
print("3. Selecione 'Criar Dispositivo Agregado'")
print("4. Na lista, marque os dispositivos que você quer combinar:")
print("   - Por exemplo: MacBook Pro Speakers + BlackHole 2ch")
print("5. Dê um nome ao dispositivo (ex: 'Meu Dispositivo Agregado')")
print("6. Feche a janela")
print()
print("Depois de criar, execute este teste novamente para ver o dispositivo!")
print()

# Testar dispositivos atuais
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.audio.device_manager import AudioDeviceManager

    print("📋 Dispositivos atuais detectados:")
    print("-" * 40)

    device_manager = AudioDeviceManager()
    devices = device_manager.get_input_devices()

    for device_id, device_name in devices:
        name_lower = device_name.lower()

        if any(keyword in name_lower for keyword in ['aggregate', 'agregado', 'combined', 'conjunto']):
            print(f"🎯 ID {device_id}: {device_name} [DISPOSITIVO AGREGADO!]")
        elif any(keyword in name_lower for keyword in ['múltipla', 'multiple', 'multi-output']):
            print(f"🔧 ID {device_id}: {device_name} [Multi-Output]")
        elif any(keyword in name_lower for keyword in ['blackhole', 'virtual']):
            print(f"🔧 ID {device_id}: {device_name} [Virtual]")
        else:
            print(f"🎤 ID {device_id}: {device_name}")

    print()
    print("💡 Se você não vê um dispositivo agregado na lista,")
    print("   precisa criar um no Audio MIDI Setup do macOS!")

except Exception as e:
    print(f"❌ Erro: {e}")
