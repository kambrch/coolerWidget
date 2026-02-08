"""Thermal monitoring service for periodic temperature polling."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from .hardware_monitor import HardwareMonitor, SensorReading


@dataclass
class TemperatureHistory:
    """Stores historical temperature data."""

    readings: list[SensorReading]
    max_size: int = 1000

    def add_reading(self, reading: SensorReading) -> None:
        """Add a new reading to the history."""
        self.readings.append(reading)
        if len(self.readings) > self.max_size:
            del self.readings[:-self.max_size]

    def get_readings_for_timeframe(self, minutes: int) -> list[SensorReading]:
        """Get readings from the last specified number of minutes."""
        timeframe = datetime.now() - timedelta(minutes=minutes)
        return [reading for reading in self.readings if reading.timestamp >= timeframe]


class ThermalMonitoringService:
    """Service for periodic thermal monitoring."""

    def __init__(self, polling_interval: float = 5.0) -> None:
        self.monitor = HardwareMonitor()
        self.polling_interval = polling_interval

        self._state_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.is_running = False

        self.history: dict[str, TemperatureHistory] = {}
        self.reading_callbacks: list[Callable[[list[SensorReading]], None]] = []
        self.error_callbacks: list[Callable[[Exception], None]] = []

        # Callbacks are enqueued from worker thread and processed by caller thread.
        self._pending_readings: queue.SimpleQueue[list[SensorReading]] = queue.SimpleQueue()
        self._pending_errors: queue.SimpleQueue[Exception] = queue.SimpleQueue()

    def start_monitoring(self) -> None:
        """Start the periodic monitoring thread."""
        with self._state_lock:
            if self._thread and self._thread.is_alive():
                return

            self._stop_event.clear()
            self.is_running = True
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()

    def stop_monitoring(self) -> None:
        """Stop the periodic monitoring and wait for worker exit."""
        with self._state_lock:
            self.is_running = False
            self._stop_event.set()
            thread = self._thread

        if thread:
            thread.join()

        with self._state_lock:
            self._thread = None

    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in a separate thread."""
        while not self._stop_event.is_set():
            try:
                readings = self.monitor.get_current_readings()
                self._record_readings(readings)
                self._pending_readings.put(readings)
            except RuntimeError as exc:
                self._pending_errors.put(exc)

            self._stop_event.wait(self.polling_interval)

        with self._state_lock:
            self.is_running = False

    def _record_readings(self, readings: list[SensorReading]) -> None:
        """Store readings in per-sensor history."""
        with self._state_lock:
            for reading in readings:
                sensor_key = reading.name
                history = self.history.get(sensor_key)
                if history is None:
                    history = TemperatureHistory([])
                    self.history[sensor_key] = history
                history.add_reading(reading)

    def process_pending_callbacks(self) -> None:
        """Run queued callbacks on the caller thread (recommended for UI thread)."""
        while True:
            try:
                readings = self._pending_readings.get_nowait()
            except queue.Empty:
                break

            for callback in self.reading_callbacks:
                try:
                    callback(readings)
                except Exception as exc:  # Callback code is external/user-provided.
                    self._pending_errors.put(exc)

        while True:
            try:
                error = self._pending_errors.get_nowait()
            except queue.Empty:
                break

            for error_callback in self.error_callbacks:
                try:
                    error_callback(error)
                except Exception:
                    # Secondary error handlers must not break callback processing.
                    continue

    def register_reading_callback(self, callback: Callable[[list[SensorReading]], None]) -> None:
        """Register a callback to be called when new readings are available."""
        self.reading_callbacks.append(callback)

    def register_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """Register a callback to be called when an error occurs."""
        self.error_callbacks.append(callback)

    def get_current_readings(self) -> list[SensorReading]:
        """Get the most recent readings from the monitor."""
        return self.monitor.get_current_readings()

    def get_historical_readings(self, sensor_name: str, minutes: int = 60) -> list[SensorReading]:
        """Get historical readings for a specific sensor."""
        with self._state_lock:
            history = self.history.get(sensor_name)
            if history is None:
                return []
            return list(history.get_readings_for_timeframe(minutes))

    def get_all_historical_readings(self, minutes: int = 60) -> dict[str, list[SensorReading]]:
        """Get historical readings for all sensors."""
        result: dict[str, list[SensorReading]] = {}
        with self._state_lock:
            for sensor_name, history in self.history.items():
                result[sensor_name] = list(history.get_readings_for_timeframe(minutes))
        return result
