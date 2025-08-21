#!/usr/bin/env python3
"""
Teste específico para verificar dispositivos virtuais e de múltiplas saídas
"""
import sounddevice as sd

def find_virtual_devices():
    print("🔍 Procurando dispositivos virtuais e especiais...")
    print("=" * 60)

    devices = sd.query_devices()
    virtual_devices = []

    for i, device in enumerate(devices):
        name = device['name']
        max_in = device['max_input_channels']
        max_out = device['max_output_channels']

        # Buscar por palavras-chave que indicam dispositivos virtuais
        name_lower = name.lower()
        is_virtual = False
        device_type = ""

        if any(keyword in name_lower for keyword in ['blackhole', 'loopback', 'virtual', 'aggregate']):
            is_virtual = True
            device_type = "Virtual Audio Driver"
        elif any(keyword in name_lower for keyword in ['múltipla', 'multiple', 'multi-output', 'multi output']):
            is_virtual = True
            device_type = "Multi-Output Device"
        elif any(keyword in name_lower for keyword in ['soundflower', 'vb-audio', 'voicemeeter']):
            is_virtual = True
            device_type = "Virtual Audio Software"

        if is_virtual or max_in > 0:  # Incluir todos com entrada ou virtuais
            capabilities = []
            if max_in > 0:
                capabilities.append(f"IN({max_in})")
            if max_out > 0:
                capabilities.append(f"OUT({max_out})")
            cap_str = "/".join(capabilities)

            virtual_devices.append({
                'id': i,
                'name': name,
                'type': device_type if is_virtual else "Audio Input",
                'capabilities': cap_str,
                'is_virtual': is_virtual
            })

    print("📋 Dispositivos encontrados:")
    for dev in virtual_devices:
        icon = "🔧" if dev['is_virtual'] else "🎤"
        print(f"  {icon} ID {dev['id']:2d}: {dev['name']:<35} [{dev['capabilities']}] - {dev['type']}")

    return virtual_devices

if __name__ == "__main__":
    devices = find_virtual_devices()

    print(f"\n✅ Total: {len(devices)} dispositivos com entrada ou virtuais")
    print("\n🎤 Apenas dispositivos de ENTRADA:")
    for dev in devices:
        if 'IN(' in dev['capabilities']:
            print(f"  - ID {dev['id']}: {dev['name']}")
