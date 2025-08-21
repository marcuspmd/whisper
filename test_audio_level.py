#!/usr/bin/env python3
"""
Teste rápido para verificar se o nível de áudio está sendo calculado corretamente.
"""

import time
import sys
import os

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from audio.capture import AudioCapture

def test_audio_level():
    print("Testando cálculo de nível de áudio...")

    # Cria captura de áudio
    capture = AudioCapture(device_index=6)  # Microfone do MacBook

    if not capture.start():
        print("❌ Erro ao iniciar captura")
        return

    print("🎤 Captura iniciada. Fale algo no microfone por 10 segundos...")

    try:
        for i in range(100):  # 10 segundos (100 * 0.1s)
            level = capture.get_audio_level()
            percent = int(level * 100)
            bar = "█" * (percent // 5) + "░" * (20 - (percent // 5))
            print(f"\rNível: [{bar}] {percent:3d}%", end="", flush=True)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Teste interrompido pelo usuário")

    finally:
        capture.stop()
        print("\n✅ Teste finalizado")

if __name__ == "__main__":
    test_audio_level()
