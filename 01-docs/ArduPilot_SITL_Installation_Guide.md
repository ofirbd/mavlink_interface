# ArduPilot SITL Installation and Testing Guide

- **Version:** 1.1
- **Date:** 2026-02-10
- **Author:** Gemini CLI

---

### 1. Introduction

This document provides detailed guidance on setting up and running the ArduPilot Software In The Loop (SITL) simulator on a Windows machine, leveraging the Windows Subsystem for Linux (WSL). SITL is crucial for testing our MAVLink C++ application without requiring physical drone hardware.

### 2. What is ArduPilot SITL?

ArduPilot SITL is a powerful simulation environment that allows you to run the actual ArduPilot flight control firmware on your computer. It simulates the drone's behavior, sensors, and flight dynamics, outputting realistic MAVLink telemetry data. It's an integral part of the ArduPilot development ecosystem.

### 3. Why Use WSL for SITL?

While it's technically possible to set up a native Windows build environment for SITL, using WSL (Windows Subsystem for Linux) is highly recommended for several reasons:

*   **Simplified Setup:** The ArduPilot build tools and dependencies are primarily designed for Linux environments, making setup significantly easier within WSL.
*   **Performance:** WSL 2 (the current version) offers good performance for Linux applications.
*   **Consistency:** It provides a consistent environment that mirrors the build process used by the ArduPilot developers.

### 4. Prerequisites

Before you begin, ensure you have the following installed on your Windows machine:

1.  **Windows Subsystem for Linux (WSL):**
    *   Open PowerShell as Administrator and run: `wsl --install`
    *   Follow the prompts to install a Linux distribution (e.g., Ubuntu is a common choice).
    *   Set up a username and password for your Linux distribution.
2.  **Git:** For cloning the ArduPilot repository.
3.  **Visual Studio Code (Optional but Recommended):** Excellent for editing files within WSL.
4.  **Virtual Serial Port Driver (e.g., com0com):** For bridging MAVProxy to our C++ application. Download and install a virtual serial port driver for Windows. (e.g., `com0com` is a popular open-source option). During installation, create a paired COM port, e.g., `COM10` and `COM11`.

### 5. Step-by-Step Setup and Execution

#### 5.1. Inside WSL: Setting up the ArduPilot Build Environment

1. **Open your WSL Terminal:**
   *   Search for "Ubuntu" (or your chosen Linux distribution) in the Windows Start Menu or install if not installed yet: `wsl --install -d Ubuntu`
2. **Install Essential Packages:**
   ```bash
   sudo apt update
   sudo apt install git python3 python3-pip python3-dev python3-opencv python3-matplotlib python3-scipy python3-setuptools python3-wheel python3-numpy python3-toml python3-empy python3-yaml python3-future python3-pexpect build-essential ccache libtool autoconf automake libxml2-dev libxslt-dev xsltproc
   sudo apt install python3-serial
   ```
3. **Clone the ArduPilot Repository:**
   ```bash
   cd ~ # Go to your home directory in WSL
   git clone https://github.com/ArduPilot/ardupilot.git
   cd ardupilot
   git submodule update --init --recursive
   ```
4.  **Add ArduPilot Tools to PATH:**
    Edit your `.bashrc` or `.zshrc` file:
    
    ```bash
    nano ~/.bashrc # or ~/.zshrc
    ```
    Add the following lines at the end:
    ```bash
    export PATH=$PATH:$HOME/ardupilot/Tools/autotest
    ```
    Save and exit (Ctrl+O, Enter, Ctrl+X). Then apply changes:
    ```bash
    source ~/.bashrc # or source ~/.zshrc
    ```

**Install MAVProxy:**

`sudo apt update`
`sudo apt install pipx`
`pipx ensurepath`

`pipx install mavproxy`

`pipx inject mavproxy future lxml`

**Restart your terminal** (or run `source ~/.bashrc`) .



#### 5.2. Inside WSL: Running ArduPilot SITL

1.  **Navigate to a Vehicle Directory:**
    
    ```bash
    cd ~/ardupilot/ArduCopter # Or ArduPlane, ArduRover etc.
    ```
2.  **Launch SITL:**
    ```bash
    sim_vehicle.py -v Copter --map --console
    ```
    *   `-v Copter`: Specifies the vehicle type (e.g., Copter, Plane).
    *   `--map`: Launches a basic map interface for visualizing the drone's position.
    *   `--console`: Launches a text-based console for interacting with the simulated flight controller.
    *   **MAVLink Output:** By default, SITL will output MAVLink telemetry over UDP on `127.0.0.1:14550` (localhost, port 14550). You should see messages indicating the simulation is running.

#### 5.3. Inside WSL: Setting up MAVProxy Bridge

While SITL is running in one WSL terminal, open a **new WSL terminal**.

1. **Run MAVProxy to Bridge UDP to Serial:**
   You need to tell MAVProxy to listen to the SITL's UDP output and forward it to a TCP port that Windows can then access and map to a virtual COM port.

   *   First, confirm the UDP port SITL is using (usually `14550`).
   *   **Option A: Bridging to a TCP port (more reliable across WSL/Windows):**
       ```bash
       MAVProxy.py --master=udp:127.0.0.1:14550 --out=tcpin:0.0.0.0:5760
       ```
       This command makes MAVProxy listen to SITL's UDP output and then broadcast it on TCP port 5760 (accessible from Windows as `127.0.0.1:5760`).
   *   **Option B: Bridging directly to a Windows COM port (requires careful firewall/networking config, not always reliable from WSL directly):**
       ```bash
       MAVProxy.py --master=udp:127.0.0.1:14550 --out=COMX,BAUD_RATE
       ```
       (Replace `COMX` with your virtual COM port, e.g., `COM10`, and `BAUD_RATE` with the desired baud rate, e.g., `115200`). This method can be tricky due to how WSL interacts with Windows COM ports. **Option A is generally more robust.**

#### 5.4. On Windows: Connecting the C++ Application

1.  **Using TCP-to-Serial Port Mapper (for Option A in 5.3):**
    If you used MAVProxy to output to `tcpin:0.0.0.0:5760`, you'll need a Windows utility that can map this TCP stream to one of your virtual COM ports (e.g., `COM11` from your `com0com` pair). There are several such utilities available, like `HW VSP` or `com0com` might have mapping capabilities.
    *   Configure this utility to listen to `127.0.0.1:5760` and expose it as, for example, `COM11`.
2.  **Run your C++ Application:**
    Configure your C++ application to connect to the Windows virtual COM port that is now receiving the MAVLink stream (e.g., `COM11`).

### 6. Simulation Chain Summary

`ArduPilot SITL (WSL)`
    `| (UDP: 127.0.0.1:14550)`
    `v`
`MAVProxy (WSL)`
    `| (TCP: 127.0.0.1:5760)`
    `v`
`TCP-to-Serial Mapper (Windows)`
    `| (Virtual COM Port: e.g., COM11)`
    `v`
`Your C++ Application (Windows)`

This setup provides a comprehensive and realistic testing environment for your MAVLink C++ communication program.

### 7. Testing the Simulator and Data Pipeline

After setting up SITL, MAVProxy, and your virtual COM ports, it's crucial to verify that the entire data pipeline is working correctly before your C++ application attempts to read data.

#### 7.1. Verify ArduPilot SITL Operation (Inside WSL)

When you run `sim_vehicle.py -v Copter`, observe the output in your WSL terminal:

*   **Console Output:** You should see messages indicating the simulation is starting, including GPS lock (`GPS: 3D fix`), altitude readings, and potentially the simulated drone arming or taking off if you command it.

**Confirmation:** If SITL starts without errors, shows GPS fix, and the drone appears on the map, it's successfully generating MAVLink data.

#### 7.2. Verify MAVProxy Operation (Inside WSL)

In the separate WSL terminal where you ran MAVProxy (e.g., `MAVProxy.py --master=udp:127.0.0.1:14550 --out=tcpin:0.0.0.0:5760`), observe its output:

*   **Connection Messages:** MAVProxy will display messages indicating it has connected to the SITL's UDP output.
*   **Traffic Indication:** If you're using `--out=tcpin`, MAVProxy will usually show a message like "MAV> TCP: waiting for connection on 0.0.0.0:5760". Once your TCP-to-Serial mapper (on Windows) connects, MAVProxy will confirm the client connection.
*   **MAVLink Packet Counts:** MAVProxy often provides a summary of MAVLink packets being received and forwarded, confirming data flow.

**Confirmation:** MAVProxy should show active connections and indications of MAVLink traffic.

#### 7.3. Verify Virtual COM Port and TCP-to-Serial Mapping (On Windows)

This step verifies that the MAVLink data is successfully flowing from WSL into a Windows-accessible virtual COM port.

1.  **Device Manager Check:**
    *   Open Windows Device Manager (search for "Device Manager").
    *   Expand "Ports (COM & LPT)".
    *   Ensure your virtual COM port pair (e.g., `COM10` and `COM11` from `com0com`) are listed and show no errors.
2.  **Use a Serial Terminal Program:**
    *   Download and install a serial terminal program on Windows (e.g., RealTerm, PuTTY, Termite, or the Serial Monitor in the Arduino IDE if configured for a COM port).
    *   **Connect the terminal program to the virtual COM port that your C++ application will *eventually* use** (e.g., `COM11`).
    *   Set the baud rate (though for virtual ports, it's often not critical, match what you configured if your TCP-to-Serial mapper uses one).
    *   **Observe Data:** If everything is correctly bridged, you should see a continuous stream of seemingly random characters (gibberish in ASCII) in the terminal. This is raw MAVLink binary data. The key is that you see *any* data flowing, not just a blank screen.

**Confirmation:** Seeing a constant stream of raw binary data on the virtual COM port indicates that the SITL output is successfully making its way through MAVProxy and the TCP-to-Serial mapper to your Windows system.

#### 7.4. Verify with Your C++ Application

The ultimate test is when your C++ application successfully opens the COM port, reads the incoming bytes, parses them, and displays the telemetry data.

*   **Port Opening:** Ensure your application can successfully open the specified COM port (e.g., `COM11`).
*   **Raw Byte Reading:** As an initial step, confirm your application can read *any* bytes from the serial port. You might print raw incoming bytes to the console to verify.
*   **MAVLink Parsing:** Once you integrate the MAVLink parsing logic, the final confirmation will be seeing the structured navigation data (latitude, longitude, heading, etc.) printed cleanly to your application's console.
