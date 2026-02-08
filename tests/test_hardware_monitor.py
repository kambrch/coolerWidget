"""Unit tests for hardware monitor functionality."""

import pytest

from coolerwidget.core.hardware_monitor import HardwareMonitor


def test_parse_sensor_data_filters_only_temperature_inputs() -> None:
    monitor = HardwareMonitor()
    raw_data = {
        "k10temp-pci-00c3": {
            "Tctl": {
                "temp1_input": 52.0,
                "temp1_max": 95.0,
            }
        },
        "nct6798-isa-0a20": {
            "in0": {"in0_input": 1.01},
            "fan1": {"fan1_input": 900},
            "temp2": {"temp2_input": 43.0},
        },
    }

    readings = monitor.parse_sensor_data(raw_data)

    assert len(readings) == 2
    assert all(reading.unit == "°C" for reading in readings)
    assert all("input" in reading.name for reading in readings)
    assert {reading.value for reading in readings} == {52.0, 43.0}


def test_get_raw_sensor_data_raises_for_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monitor = HardwareMonitor()

    def fake_execute() -> str:
        return "not-json"

    monkeypatch.setattr(monitor, "_execute_sensors_command", fake_execute)

    with pytest.raises(RuntimeError, match="Failed to parse sensor data as JSON"):
        monitor.get_raw_sensor_data()
