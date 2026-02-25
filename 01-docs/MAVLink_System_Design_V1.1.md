# System Design Document: MAVLink Drone Communication System

- **Version:** 1.1
- **Date:** 2026-02-10
- **Status:** Proposed
- **Author:** Gemini CLI (Senior Embedded/Full-Stack)

---

### Revision History

| Version | Date       | Author       | Changes                                                                                                                                                             |
|---------|------------|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.0     | 2026-02-10 | Gemini CLI   | Initial draft outlining basic components and testing strategy.                                                                                                      |
| 1.1     | 2026-02-10 | Gemini CLI   | Revised with a multi-threaded architecture, proposed Boost.Asio for serial I/O, added formal error handling, state management, and configuration sections. |

---

### 1. Overview

#### 1.1. Purpose
This document specifies the design for a robust, scalable C++ application for Windows to establish communication with a MAVLink-enabled UAS (Unmanned Aircraft System). The application will acquire, decode, and display key telemetry data, with an architecture designed for future expansion.

#### 1.2. Scope
The system will provide real-time display of primary navigation data. The architecture must be decoupled and extensible to support future features like data logging, command issuance (GCS functions), or a graphical user interface (GUI).

### 2. System Architecture

To ensure a non-blocking and responsive application, a multi-threaded architecture will be employed. The I/O operations will be isolated from the main application logic.

**Architectural Diagram:**
```
+------------------+      +-----------------------------------------------------------------+
|  Drone /         |      |                  Windows C++ Application                        |
|  Simulator       +----->| +------------------+   +-------------------+   +---------------+ |
|  (MAVLink Source)| RS232| | Serial I/O Thread|-->| Thread-Safe Queue |-->|  Main Thread  | |
+------------------+      | | (Boost.Asio)     |   | (MAVLink Msgs)    |   | (App Logic &  | |
                        | | - Read Bytes     |   +-------------------+   |  UI/Display)  | |
                        | | - Parse MAVLink  |             ^             |               | |
                        | | - Enqueue Msgs   |             |             |               | |
                        | +------------------+   +-------------------+   +---------------+ |
                        |                        |  Data Model (Nav) |<--|               |
                        |                        +-------------------+                     |
                        +-----------------------------------------------------------------+
```

### 3. Component Breakdown

#### 3.1. MAVLink Protocol Library (`c_library_v2`)
The official header-only MAVLink C/C++ library remains the core of the protocol layer. Headers will be generated from the `common.xml` dialect definition using the provided Python-based generator. This component is passive and will be utilized by the I/O thread.

#### 3.2. Serial Communication (I/O Thread)
This component is the engine of the application, running on a dedicated thread to handle all serial communication and protocol parsing.

- **Library:** **Boost.Asio** is proposed for handling serial port I/O. Direct use of the Win32 API is discouraged to promote cleaner, more portable, and asynchronous-capable code.
- **Responsibilities:**
    1.  **Connection Management:** Open, configure (baud rate, etc.), and close the serial port.
    2.  **Asynchronous Reading:** Use `boost::asio::async_read` to continuously read data from the serial port without blocking.
    3.  **MAVLink Parsing:** In the read handler, feed the incoming byte stream into the `mavlink_parse_char()` state machine.
    4.  **Message Enqueueing:** When a complete MAVLink message (`mavlink_message_t`) is successfully parsed, it will be moved into a thread-safe queue for consumption by the main thread.

#### 3.3. Thread-Safe Message Queue
A standard producer-consumer queue will decouple the I/O thread from the main thread.

- **Implementation:** A `std::queue` wrapped in a `std::mutex` and signaled by a `std::condition_variable` is a standard C++ pattern for this task. It will store fully-formed `mavlink_message_t` objects.

#### 3.4. Main Application Thread
The main thread is responsible for application logic, state management, and data presentation.

- **Responsibilities:**
    1.  **Initialization:** Start the I/O thread.
    2.  **Message Dequeueing:** In its main loop, it will wait on the message queue for new messages from the I/O thread.
    3.  **Message Dispatch:** Upon receiving a message, it will use a `switch` on the `msg.msgid` to delegate to the appropriate data handler.
    4.  **Data Model Update:** Update the central `NavigationData` model with the new telemetry.
    5.  **Display:** Periodically render the contents of the `NavigationData` model to the console.

#### 3.5. Data Model
A thread-safe class will encapsulate the navigation data.

```cpp
class NavigationData {
public:
    // Public methods to get data fields
    // Public methods to update data fields (internally locked with mutex)
private:
    // Data fields (lat, lon, etc.)
    std::mutex m_mutex;
};
```

### 4. Configuration
Application parameters will not be hardcoded. They will be supplied via command-line arguments at launch.

- **Required:**
    - `--port <COM_PORT_NAME>` (e.g., `COM3`)
    - `--baud <BAUD_RATE>` (e.g., `57600`)
- **Benefit:** Allows the same compiled executable to be used with different hardware setups without recompilation.

### 5. Error Handling and State Management
The application will operate as a simple state machine to ensure predictable behavior.

- **States:** `DISCONNECTED`, `CONNECTING`, `CONNECTED`, `ERROR`.
- **Logging:** A simple console logging mechanism will be implemented to report:
    - State transitions (e.g., "Attempting to connect to COM3...").
    - Errors (e.g., "Error: Port not found.", "Error: Read timeout.").
    - Key events (e.g., "First GPS_RAW_INT message received.").

### 6. Testing Strategy
The testing strategy remains unchanged from v1.0, as it is already robust. It leverages a **SITL (ArduPilot)** simulator, a **UDP-to-Serial bridge (MAVProxy)**, and a **virtual COM port driver**. This setup decouples development from physical hardware, enabling rapid and reliable testing.

### 7. Build Environment
- **IDE/Compiler:** Visual Studio 2022 (with MSVC).
- **Build System:** CMake.
- **Dependencies:**
    - Boost Libraries (specifically Asio).
    - Git, Python (for MAVLink generator).

This revised design provides a superior foundation for a real-world application, emphasizing scalability, reliability, and maintainability.
