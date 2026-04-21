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

#### 2.2. Telem 1 / Telem 2 Ports (Serial) - Recommended for Embedded
- **Hardware Required:** USB-to-TTL Serial Adapter (e.g., CP2102).
- **Pin Identification (Telem1 JST-GH 6-pin):**
    - **Pin 1 (Red Wire):** VCC (+5V) - **DO NOT CONNECT** if Cube is separately powered.
    - **Pin 2 (Black):** Cube **TX** (Out)
    - **Pin 3 (Black):** Cube **RX** (In)
    - **Pin 4/5 (Black):** CTS/RTS (Flow Control) - Leave Empty.
    - **Pin 6 (Black):** **GND** (Ground)
- **Wiring (Cross-Connection to CP2102):**
    | Cube Telem1 Pin | Signal | CP2102 Pin |
    | :--- | :--- | :--- |
    | Pin 2 | TX | **RXD** |
    | Pin 3 | RX | **TXD** |
    | Pin 6 | GND | **GND** |

#### 2.3. Port Parameters
Based on the requirement for 5Hz automatic output, the serial port must be configured with the following standard MAVLink settings:
- **Baud Rate:** **460800** (Recommended for Telem1) or 115200 (Common for USB).
- **Data Bits:** 8
- **Stop Bits:** 1
- **Parity:** None

### 3. Step-by-Step Interface Procedure

#### Step 1: Identify the COM Port
1. Open **Windows Device Manager**.
2. Expand **Ports (COM & LPT)**.
3. Note the port number assigned to the Cube or the CP2102 adapter.

#### Step 2: Running the Test Script
In this architecture, the **Telem1** port is the primary interface for navigation data. Run the listener script on the assigned serial adapter:

```powershell
# Primary Listener Connection (Telem1 via CP2102)
python 02-develop/cube/mavlink_serial_dashboard.py COM6 460800
```

> **Note:** If a Telem1 USB-to-Serial adapter is not available, the main Cube USB port (COM5) can be used as a fallback for listening. However, in simulation mode, COM5 is utilized by the GPS Injector and cannot be used for the listener simultaneously unless a MAVLink router/mirror is employed.

#### Step 3: Cube Configuration (One-time Setup)
If the Cube is not yet streaming at 5Hz, use **Mission Planner** or **QGroundControl**:
1. Connect to the Cube.
2. Go to **Config/Tuning** -> **Full Parameter List**.
3. Locate the `SERIALx_BAUD` (where x is the port used) and set it to **`460`** (460800) or `115` (115200).
4. Locate `SRx_POSITION` and `SRx_EXTRA1` (where x is the serial instance) and set them to `5` to achieve the 5Hz rate for navigation and attitude data.

#### Step 3: Establish Serial Session
The application must initialize the serial port using the parameters identified in Step 1 and 2.

#### Step 4: Protocol Version and Heartbeat Synchronization
The application must handle both MAVLink 1 and MAVLink 2 protocols. The interface library (pymavlink or C/C++ headers) performs **automatic header detection**:

| Protocol Version | Header Start Byte (Hex) | Description |
| :--- | :--- | :--- |
| **MAVLink 1** | `0xFE` | Legacy protocol, used on Serial 1 by default. |
| **MAVLink 2** | `0xFD` | Modern protocol, used on Serial 0 (USB) by default. |

**Autodetect Logic:**
- The parser looks for the `0xFE` or `0xFD` start byte to determine the packet structure.
- Navigation data remains identical across both versions for standard message IDs.
- The application waits for a `HEARTBEAT` message (ID #0) to identify the System ID and Component ID, though it can proceed in "Stream-Only" mode if a heartbeat is not detected within 3 seconds.

#### Step 5: Navigation Message Decoding
The application listens for the following MAVLink messages arriving at 5Hz:

| Message ID | Message Name | Key Data Fields |
| :--- | :--- | :--- |
| #2 | `SYSTEM_TIME` | Boot Time (ms), Unix Timestamp (UTC) |
| #33 | `GLOBAL_POSITION_INT` | Lat/Lon, Rel Alt, **High-Precision Heading (centidegrees)** |
| #30 | `ATTITUDE` | Roll, Pitch, Yaw (radians to degrees conversion) |
| #74 | `VFR_HUD` | Groundspeed, Airspeed, Throttle |
| #24 | `GPS_RAW_INT` | **Fix Type (3 = 3D Fix), Satellites Visible**, HDOP |

### 4. Implementation Logic (C++ / Boost.Asio)

The interface logic will follow the multi-threaded pattern defined in the System Design V1.1:

1.  **I/O Thread:** Opens the serial port `COMx`.
2.  **Parser:** Pass raw bytes into `mavlink_parse_char()`.
3.  **Dispatcher:** When a full packet is ready, check `msg.msgid`.
4.  **Data Extraction:** Use `mavlink_msg_global_position_int_decode()` to extract navigation fields.
5.  **Main Thread:** Updates the UI or logic layer at the 5Hz arrival rate.

### 6. Simulation and Testing Environment (Without physical GPS)

To simulate a real-world flight path without a physical GPS module connected to the Cube, a "GPS Injection" method is used. You can run this in two modes: **Visual Mode** (with Mission Planner) or **Direct Mode** (standalone).

#### 6.1. Prerequisite Cube Configuration
Regardless of the mode, the Cube must be configured once via Mission Planner:
- **`GPS_TYPE`**: Set to `14` (MAVLink).
- **`EK3_SRC1_POSXY`**: Set to `3` (GPS).
- **`EK3_SRC1_VELXY`**: Set to `3` (GPS).
- **Reboot:** You **must** power-cycle the Cube after changing these settings.

#### 6.2. Mode A: Visual Mode (With Mission Planner)
Use this mode to watch the drone move on the map while your scripts run.
1.  **Mission Planner Setup:**
    - Connect to the Cube via **COM5**.
    - Press **Ctrl + F** -> Click **MAVLink** button.
    - Configure: `UDP Client`, `Outbound`, Port `14550`, Host `127.0.0.1`.
    - **Check the "Write" box** and click **Go**.
2.  **Run Simulator (UDP):**
    ```powershell
    python 02-develop/cube/gps_path_simulator.py
    ```
3.  **Run Listener (Telem1):**
    ```powershell
    python 02-develop/cube/mavlink_serial_dashboard.py COM6 460800
    ```

#### 6.3. Mode B: Direct Mode (Standalone)
Use this mode for automated testing without the overhead of Mission Planner.
1.  **Preparation:** **Close Mission Planner** completely (to free up COM5).
2.  **Run Simulator (Direct COM):**
    ```powershell
    # Talk directly to the Cube's USB port
    python 02-develop/cube/gps_path_simulator.py COM5 115200
    ```
3.  **Run Listener (Telem1):**
    ```powershell
    python 02-develop/cube/mavlink_serial_dashboard.py COM6 460800
    ```

#### 6.4. Data Flow Path (Mode A)
`Injector (UDP)` -> `Mission Planner (Mirror)` -> `USB Cable (COM5)` -> `Cube (EKF Processing)` -> `Telem1 Pins` -> `CP2102 (COM6)` -> `Listener Script`
