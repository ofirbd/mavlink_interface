# System Design Document: MAVLink Cube Pilot Interface

- **Version:** 1.0
- **Date:** 2026-04-18
- **Status:** Draft
- **Author:** Gemini CLI

---

### 1. Overview
This document outlines the transition from the ArduPilot SITL (Simulator) to physical hardware using the **Cube Pilot** (Orange/Blue/Black). It provides a step-by-step guide to establishing a serial connection and decoding real-time navigation MAVLink messages.

### 2. Hardware Connection Setup

#### 2.1. Physical Connection Options
The Cube Pilot provides several ports for MAVLink communication. Choose one of the following:

1.  **USB (Micro-USB/USB-C):**
    *   **Direct Connection:** Connect the Cube's USB port directly to the Windows PC. 
    *   **Driver:** Ensure the "Proximity/Cube Pilot" or "ArduPilot" drivers are installed (usually part of Mission Planner or available via the CubePilot website).
    *   **Recognition:** The device will appear as a `COM` port (e.g., `COM4`) in Device Manager.

2.  **Telem 1 / Telem 2 Ports (Serial):**
    *   **Hardware Required:** USB-to-TTL Serial Adapter (e.g., FTDI).
    *   **Wiring:**
        *   Cube `TX` -> Adapter `RX`
        *   Cube `RX` -> Adapter `TX`
        *   Cube `GND` -> Adapter `GND`
    *   **Warning:** Ensure the adapter is set to 3.3V logic levels to avoid damaging the Cube.

#### 2.2. Port Parameters
Based on the requirement for 5Hz automatic output, the serial port must be configured with the following standard MAVLink settings:
- **Baud Rate:** 57600 (Standard for Telem ports) or 115200 (Common for USB).
- **Data Bits:** 8
- **Stop Bits:** 1
- **Parity:** None

### 3. Step-by-Step Interface Procedure

#### Step 1: Identify the COM Port
1. Open **Windows Device Manager**.
2. Expand **Ports (COM & LPT)**.
3. Note the port number assigned to the Cube (e.g., `COM5`).

#### Step 2: Cube Configuration (One-time Setup)
If the Cube is not yet streaming at 5Hz, use **Mission Planner** or **QGroundControl**:
1. Connect to the Cube.
2. Go to **Config/Tuning** -> **Full Parameter List**.
3. Locate the `SERIALx_BAUD` (where x is the port used) and set it to `57` (57600) or `115` (115200).
4. Locate `SRx_POSITION` and `SRx_EXTRA1` (where x is the serial instance) and set them to `5` to achieve the 5Hz rate for navigation and attitude data.

#### Step 3: Establish Serial Session
The application must initialize the serial port using the parameters identified in Step 1 and 2.

#### Step 4: Heartbeat Synchronization
Before processing telemetry, the application must wait for a `HEARTBEAT` message (ID #0) to confirm the protocol version (MAVLink 1 vs 2) and identify the System ID and Component ID of the Cube.

#### Step 5: Navigation Message Decoding
The application will listen for the following specific MAVLink messages arriving at 5Hz:

| Message ID | Message Name | Key Data Fields |
| :--- | :--- | :--- |
| #33 | `GLOBAL_POSITION_INT` | Latitude, Longitude, Relative Altitude, Ground Speed (VX, VY, VZ) |
| #30 | `ATTITUDE` | Roll, Pitch, Yaw (in radians) |
| #74 | `VFR_HUD` | Heading, Airspeed, Throttle |
| #24 | `GPS_RAW_INT` | Fix Type, Satellites Visible, HDOP |

### 4. Implementation Logic (C++ / Boost.Asio)

The interface logic will follow the multi-threaded pattern defined in the System Design V1.1:

1.  **I/O Thread:** Opens the serial port `COMx`.
2.  **Parser:** Pass raw bytes into `mavlink_parse_char()`.
3.  **Dispatcher:** When a full packet is ready, check `msg.msgid`.
4.  **Data Extraction:** Use `mavlink_msg_global_position_int_decode()` to extract navigation fields.
5.  **Main Thread:** Updates the UI or logic layer at the 5Hz arrival rate.

### 5. Troubleshooting
- **No Data:** Check if the Green LED on the Cube is flashing (indicating it's powered) and verify TX/RX wires aren't swapped.
- **Garbage Characters:** Usually indicates a Baud Rate mismatch. Try switching between 57600 and 115200.
- **Permission Denied:** Ensure no other software (like Mission Planner) is currently holding the COM port open.
