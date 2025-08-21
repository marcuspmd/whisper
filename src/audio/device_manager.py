"""
Audio device management
"""

from typing import Any, Dict, List, Optional, Tuple

import sounddevice as sd


class AudioDeviceManager:
    """Gerencia dispositivos de áudio do sistema"""

    def __init__(self):
        self._devices_cache = None

    def list_devices(self) -> List[Dict[str, Any]]:
        """Lista todos os dispositivos de áudio disponíveis"""
        try:
            devices = sd.query_devices()
            self._devices_cache = devices
            return list(devices)
        except Exception:
            try:
                devices = sd.devices
                self._devices_cache = devices
                return list(devices)
            except Exception as e:
                raise RuntimeError(f"Erro ao consultar dispositivos de áudio: {e}")

    def print_devices(self) -> None:
        """Imprime lista formatada de dispositivos"""
        try:
            devices = self.list_devices()
        except RuntimeError as e:
            print(f"❌ {e}")
            return

        print("\n=== Dispositivos de Áudio Disponíveis ===")
        print("ID  | Entradas | Saídas | Nome")
        print("-" * 50)

        for idx, dev in enumerate(devices):
            name = (
                dev.get("name") if isinstance(dev, dict) else getattr(dev, "name", "")
            )
            max_in = (
                dev.get("max_input_channels", 0)
                if isinstance(dev, dict)
                else getattr(dev, "max_input_channels", 0)
            )
            max_out = (
                dev.get("max_output_channels", 0)
                if isinstance(dev, dict)
                else getattr(dev, "max_output_channels", 0)
            )

            in_str = f"{max_in:2d}" if max_in > 0 else "--"
            out_str = f"{max_out:2d}" if max_out > 0 else "--"

            print(f"{idx:2d}  |    {in_str}    |   {out_str}   | {name}")
        print()

    def find_input_device_by_name(self, name_substring: str) -> Optional[int]:
        """
        Procura o primeiro dispositivo de entrada cujo nome contenha name_substring (case-insensitive).

        Args:
            name_substring: Substring para buscar no nome do dispositivo

        Returns:
            Índice do dispositivo ou None se não encontrado
        """
        try:
            devices = self.list_devices()
        except RuntimeError:
            return None

        candidates = []
        for idx, dev in enumerate(devices):
            name = (
                dev.get("name") if isinstance(dev, dict) else getattr(dev, "name", None)
            )
            max_in = (
                dev.get("max_input_channels")
                if isinstance(dev, dict)
                else getattr(dev, "max_input_channels", 0)
            )

            if (
                name
                and (name_substring.lower() in name.lower())
                and max_in
                and max_in > 0
            ):
                candidates.append((idx, name))

        if candidates:
            return candidates[0][0]
        return None

    def find_device_by_id(self, device_id: int) -> Optional[Tuple[int, str, int]]:
        """
        Verifica se o dispositivo com ID existe e retorna suas informações.

        Args:
            device_id: ID do dispositivo

        Returns:
            Tupla (id, nome, max_input_channels) ou None se não encontrado
        """
        try:
            devices = self.list_devices()
            if 0 <= device_id < len(devices):
                dev = devices[device_id]
                name = (
                    dev.get("name")
                    if isinstance(dev, dict)
                    else getattr(dev, "name", "")
                )
                max_in = (
                    dev.get("max_input_channels", 0)
                    if isinstance(dev, dict)
                    else getattr(dev, "max_input_channels", 0)
                )
                return (device_id, name, max_in)
        except RuntimeError:
            pass
        return None

    def get_input_devices(self) -> List[Tuple[int, str]]:
        """
        Retorna lista de dispositivos com entrada de áudio e dispositivos virtuais.
        Inclui dispositivos virtuais, agregados e de múltiplas saídas mesmo que não mostrem canais de entrada explícitos.

        Returns:
            Lista de tuplas (id, nome) de dispositivos de entrada
        """
        try:
            devices = self.list_devices()
            input_devices = []

            for idx, dev in enumerate(devices):
                name = (
                    dev.get("name")
                    if isinstance(dev, dict)
                    else getattr(dev, "name", "")
                )
                max_in = (
                    dev.get("max_input_channels", 0)
                    if isinstance(dev, dict)
                    else getattr(dev, "max_input_channels", 0)
                )
                max_out = (
                    dev.get("max_output_channels", 0)
                    if isinstance(dev, dict)
                    else getattr(dev, "max_output_channels", 0)
                )

                # Dispositivos com entrada explícita
                has_input = max_in > 0

                # Dispositivos virtuais e agregados baseado no nome (podem funcionar como entrada)
                name_lower = name.lower()
                is_virtual_or_aggregate = any(
                    keyword in name_lower
                    for keyword in [
                        # Drivers virtuais tradicionais
                        "blackhole",
                        "loopback",
                        "virtual",
                        "soundflower",
                        "vb-audio",
                        "voicemeeter",
                        # Dispositivos agregados macOS
                        "aggregate",
                        "agregado",
                        "combined",
                        "conjunto",
                        # Dispositivos de múltiplas saídas
                        "múltipla",
                        "multiple",
                        "multi-output",
                        "multi output",
                        "multi-input",
                        # Software de áudio
                        "obs",
                        "rogue amoeba",
                        "audio hijack",
                        "lineout",
                        "line in",
                        "line out",
                        # Outros dispositivos especiais
                        "composite",
                        "mixer",
                        "routing",
                        "studio",
                        "interface",
                    ]
                )

                # Incluir se tem entrada OU se é dispositivo virtual/agregado OU tem saída (para agregados)
                if (
                    has_input
                    or is_virtual_or_aggregate
                    or (
                        max_out > 0
                        and any(
                            keyword in name_lower
                            for keyword in [
                                "aggregate",
                                "agregado",
                                "múltipla",
                                "multiple",
                                "combined",
                                "conjunto",
                            ]
                        )
                    )
                ):
                    input_devices.append((idx, name))

            return input_devices
        except RuntimeError:
            return []

    def set_default_device(self, device_index: int) -> bool:
        """
        Define dispositivo padrão.

        Args:
            device_index: Índice do dispositivo

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Tenta configurar como tupla primeiro (entrada, saída)
            try:
                current_default = sd.default.device
                if isinstance(current_default, tuple):
                    sd.default.device = (device_index, current_default[1])
                else:
                    sd.default.device = (device_index, None)
            except Exception:
                # Fallback para versões que aceitam apenas um índice
                sd.default.device = device_index
            return True
        except Exception:
            return False
