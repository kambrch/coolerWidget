"""Unit tests for thermal monitoring service."""

from datetime import datetime

from coolerwidget.core.hardware_monitor import SensorReading
from coolerwidget.core.thermal_service import ThermalMonitoringService


def _reading(value: float = 41.0) -> SensorReading:
    return SensorReading(
        name="chip_temp1_input",
        label="CPU",
        value=value,
        unit="°C",
        timestamp=datetime.now(),
        sensor_type="CPU",
    )


def test_process_pending_callbacks_runs_callbacks_on_caller_thread() -> None:
    service = ThermalMonitoringService(polling_interval=0.01)
    received: list[list[SensorReading]] = []

    service.register_reading_callback(lambda readings: received.append(readings))
    service._pending_readings.put([_reading(44.0)])

    service.process_pending_callbacks()

    assert len(received) == 1
    assert received[0][0].value == 44.0


def test_history_access_is_thread_safe_and_returns_copies() -> None:
    service = ThermalMonitoringService()

    service._record_readings([_reading(42.0)])
    first = service.get_historical_readings("chip_temp1_input", minutes=60)
    second = service.get_historical_readings("chip_temp1_input", minutes=60)

    assert len(first) == 1
    assert len(second) == 1
    assert first is not second


def test_start_stop_can_restart_without_overlapping_threads() -> None:
    service = ThermalMonitoringService(polling_interval=0.001)
    service.monitor.get_current_readings = lambda: []

    service.start_monitoring()
    first_thread = service._thread
    assert first_thread is not None

    service.stop_monitoring()
    assert not first_thread.is_alive()

    service.start_monitoring()
    second_thread = service._thread
    assert second_thread is not None
    assert second_thread is not first_thread

    service.stop_monitoring()
    assert not second_thread.is_alive()
