#!/usr/bin/env python3
"""
Teste para verificar TODOS os dispositivos de áudio disponíveis (entrada e saída)
"""
import sounddevice as sd

print("🎤 Listando TODOS os dispositivos de áudio do sistema:")
print("=" * 60)

devices = sd.query_devices()
for i, device in enumerate(devices):
    device_type = []
    if device['max_input_channels'] > 0:
        device_type.append(f"IN({device['max_input_channels']})")
    if device['max_output_channels'] > 0:
        device_type.append(f"OUT({device['max_output_channels']})")

    type_str = "/".join(device_type) if device_type else "NONE"

    print(f"  ID {i:2d}: {device['name']:<40} [{type_str}]")

print("\n" + "=" * 60)
print("🎧 Dispositivos com ENTRADA (microfones):")
for i, device in enumerate(devices):
    if device['max_input_channels'] > 0:
        print(f"  ID {i:2d}: {device['name']} (canais: {device['max_input_channels']})")

print("\n🔊 Dispositivos com SAÍDA (alto-falantes):")
for i, device in enumerate(devices):
    if device['max_output_channels'] > 0:
        print(f"  ID {i:2d}: {device['name']} (canais: {device['max_output_channels']})")
