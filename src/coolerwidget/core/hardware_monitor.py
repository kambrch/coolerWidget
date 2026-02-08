"""Hardware monitoring module for retrieving thermal sensor data."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class SensorReading:
    """Represents a single sensor reading."""

    name: str
    label: str
    value: float
    unit: str
    timestamp: datetime
    sensor_type: str  # e.g., "CPU", "GPU", "HDD/SSD", "Motherboard"


class HardwareMonitor:
    """Class to handle hardware monitoring using lm_sensors."""

    def __init__(self) -> None:
        self.lm_sensors_available = self._check_lm_sensors_availability()

    def _check_lm_sensors_availability(self) -> bool:
        """Check if lm_sensors is available on the system."""
        return shutil.which("sensors") is not None

    def _execute_sensors_command(self) -> str:
        """Execute the sensors command and return its output."""
        if not self.lm_sensors_available:
            raise RuntimeError("lm_sensors is not available on this system")

        try:
            result = subprocess.run(
                ["sensors", "-j"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Timeout while executing sensors command") from exc
        except OSError as exc:
            raise RuntimeError(f"Error executing sensors command: {exc}") from exc

        if result.returncode != 0:
            raise RuntimeError(f"sensors command failed: {result.stderr.strip()}")

        return result.stdout

    def get_raw_sensor_data(self) -> dict[str, Any] | None:
        """Get raw sensor data from lm_sensors in JSON format."""
        output = self._execute_sensors_command()
        if not output:
            return None

        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Failed to parse sensor data as JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Unexpected sensors output format: expected top-level JSON object")

        return data

    def parse_sensor_data(self, raw_data: dict[str, Any]) -> list[SensorReading]:
        """Parse raw sensor data into SensorReading objects."""
        readings: list[SensorReading] = []

        for chip_name, chip_data in raw_data.items():
            if not isinstance(chip_data, dict):
                continue

            sensor_type = self._determine_sensor_type(chip_name)
            for feature_name, feature_data in chip_data.items():
                if not isinstance(feature_data, dict):
                    continue

                label = str(feature_data.get("label", feature_name))
                for subfeature_name, value in feature_data.items():
                    if not self._is_temperature_input(feature_name, subfeature_name):
                        continue
                    if not isinstance(value, (int, float)):
                        continue

                    readings.append(
                        SensorReading(
                            name=f"{chip_name}_{feature_name}_{subfeature_name}",
                            label=label,
                            value=float(value),
                            unit="°C",
                            timestamp=datetime.now(),
                            sensor_type=sensor_type,
                        )
                    )

        return readings

    def _is_temperature_input(self, feature_name: str, subfeature_name: str) -> bool:
        """Return True when the subfeature represents a temperature reading."""
        subfeature = subfeature_name.lower()
        feature = feature_name.lower()

        if not subfeature.endswith("_input"):
            return False

        if "temp" in subfeature or feature.startswith("temp"):
            return True

        # Support labels like "Tctl"/"Tdie" where subfeature is still tempX_input.
        return feature.startswith("tctl") or feature.startswith("tdie")

    def _determine_sensor_type(self, chip_name: str) -> str:
        """Determine sensor type based on chip name."""
        chip_lower = chip_name.lower()

        if "cpu" in chip_lower or "core" in chip_lower or "k10temp" in chip_lower:
            return "CPU"
        if "gpu" in chip_lower or "nvidia" in chip_lower or "amdgpu" in chip_lower:
            return "GPU"
        if "nvme" in chip_lower or "drivetemp" in chip_lower:
            return "HDD/SSD"
        return "Motherboard"

    def get_current_readings(self) -> list[SensorReading]:
        """Get current sensor readings."""
        raw_data = self.get_raw_sensor_data()
        if raw_data:
            return self.parse_sensor_data(raw_data)
        return []
