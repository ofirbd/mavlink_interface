# MAVLink Drone Communication System

This project provides a robust interface for communicating with MAVLink-enabled UAS (Unmanned Aircraft Systems). It supports both simulated environments (ArduPilot SITL) and physical hardware (Cube Pilot).

## Overview

The system is designed to acquire, decode, and display real-time navigation and telemetry data. It includes tools for flight simulation, GPS injection, and live dashboard monitoring.

## 1. Supported Environments

### A. ArduPilot SITL (Simulator)
- **Environment:** Dockerized ArduPilot SITL.
- **Connection:** TCP (`127.0.0.1:5760`).
- **Features:** Mission testing, mode switching (GUIDED, LAND), and basic telemetry verification.

### B. Cube Pilot (Physical Hardware)
- **Hardware:** Cube Orange/Blue/Black.
- **Connection 1 (Direct):** USB Cable (Virtual COM).
- **Connection 2 (Embedded):** Telem1 Port via USB-to-TTL (CP2102) adapter at **460800 baud**.
- **Features:** High-speed real-time telemetry, EKF monitoring, and hardware-in-the-loop (HIL) simulation.

---

## 2. Key Scripts (`02-develop/`)

### Cube Hardware (`02-develop/cube/`)
- **`mavlink_serial_dashboard.py`**: High-precision navigation dashboard for Telem1.
- **`gps_path_simulator.py`**: Circular trajectory injector (1km @ 20m/s).
- **`gps_static_injector.py`**: Stationary location injector.

### SITL Simulation (`02-develop/sitl/`)
- **`dashboard_sitl.py`**: Dashboard specifically for SITL.
- **`mission_control.py`**: Automated mission script (Takeoff -> Monitor -> Land).
- **`telemetry.py`**: Basic SITL telemetry monitor.
- **`takeoff_test.py`**: SITL specialized takeoff test.

---

## 3. Quick Start: Physical Cube Testing

1.  **Mission Planner Bridge:**
    - Connect Cube via USB (COM5).
    - Enable **MAVLink Mirror** (`Ctrl+F` -> MAVLink -> UDP Client -> Outbound -> Port 14550 -> Write Checkbox).
2.  **Start Simulator:**
    ```powershell
    python 02-develop/cube/gps_path_simulator.py
    ```
3.  **Start Listener (Telem1):**
    ```powershell
    python 02-develop/cube/mavlink_serial_dashboard.py COM6 460800
    ```

---

## 4. Documentation

Detailed design documents are available in the `01-docs/` directory:
- **`MAVLink_System_Design_V1.1.md`**: Architectural design for a multi-threaded C++ implementation.
- **`MAVLink_Cube_Interface_Design_V1.0.md`**: Step-by-step guide for physical hardware setup, wiring (CP2102), and simulation configuration.
- **`ArduPilot_SITL_Installation_Guide.md`**: Guide for setting up the Docker-based simulation environment.

## Requirements
- Python 3.x
- `pymavlink`
- `pyserial`
- (Optional) Docker for SITL
- (Optional) Mission Planner for Cube configuration
