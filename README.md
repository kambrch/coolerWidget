# coolerWidget

A thermal monitoring application with PySide6 GUI for visualizing hardware temperatures.

CoolerWidget is a comprehensive thermal monitoring solution that leverages lm_sensors to monitor hardware temperatures in real-time. The application provides visualization of CPU, GPU, HDD, and motherboard temperatures with historical data tracking.

## Features

- Real-time hardware temperature monitoring using lm_sensors
- Support for multiple sensor types (CPU, GPU, HDD, Motherboard)

## Planned Features
- Historical temperature data visualization
- Configurable polling intervals
- Color-coded temperature alerts
- Cross-platform compatibility

## Installation

To install dependencies, run:

```bash
poetry install
```

Make sure lm_sensors is installed on your system:
```bash
# On Ubuntu/Debian
sudo apt-get install lm-sensors

# On Fedora/RHEL
sudo dnf install lm_sensors

# On Arch Linux
sudo pacman -S lm_sensors
```

## Usage

To run the application, use:

```bash
poetry run coolerWidget
```
