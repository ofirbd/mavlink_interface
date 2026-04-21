import sys
import time
import os
from pymavlink import mavutil
from datetime import datetime

def main():
    # --- CONFIGURATION ---
    # Update these values to match your hardware setup
    DEFAULT_PORT = 'COM4'      # Update to your Cube's COM port
    DEFAULT_BAUD = 57600      # Standard for Telem ports. Use 115200 for USB.
    # ---------------------

    print("--- MAVLink Cube Serial Interface Test ---")
    
    # Allow command line overrides: python script.py COM5 115200
    port = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PORT
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_BAUD

    print(f"Connecting to {port} at {baud} baud...")

    try:
        # 1. Establish Serial Connection
        connection = mavutil.mavlink_connection(port, baud=baud)

        # 2. Wait for Heartbeat (Optional/Non-blocking)
        print(f"Connecting to Cube on {port}...")
        print("Checking for Heartbeat (will skip after 3 seconds if only streaming data)...")
        
        # Try to get a heartbeat, but don't hang forever
        hb = connection.wait_heartbeat(timeout=3)
        if hb:
            print(f"Heartbeat received! System ID: {connection.target_system}, Component ID: {connection.target_component}")
        else:
            print("No Heartbeat detected. Proceeding in 'Stream-Only' mode...")
            # Manually set target IDs if no heartbeat (Standard ArduPilot defaults)
            connection.target_system = 1
            connection.target_component = 1

        # Force a stream request just in case (optional for 5Hz auto-stream)
        connection.mav.request_data_stream_send(
            connection.target_system, connection.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL, 5, 1)

        # 3. Data Loop
        # Internal state to store latest values
        nav_data = {
            'lat': 0.0, 'lon': 0.0, 'alt': 0.0,
            'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
            'heading': 0, 'groundspeed': 0.0,
            'boot_time_ms': 0,
            'unix_time_str': '00:00:00',
            'sats': 0,
            'fix_type': 0,
            'last_update': 'N/A'
        }

        while True:
            # Check for specific navigation messages
            # We use a short timeout to keep the loop responsive
            msg = connection.recv_match(type=['GLOBAL_POSITION_INT', 'ATTITUDE', 'VFR_HUD', 'SYSTEM_TIME', 'GPS_RAW_INT'], blocking=True, timeout=0.1)
            
            if msg:
                msg_type = msg.get_type()
                
                if msg_type == 'GLOBAL_POSITION_INT':
                    nav_data['lat'] = msg.lat / 1e7
                    nav_data['lon'] = msg.lon / 1e7
                    nav_data['alt'] = msg.relative_alt / 1000.0 # Relative Alt in meters
                    # Use high-precision heading (centidegrees -> degrees)
                    if msg.hdg != 65535:
                        nav_data['heading'] = msg.hdg / 100.0
                
                elif msg_type == 'ATTITUDE':
                    import math
                    # Convert radians to degrees
                    nav_data['roll'] = math.degrees(msg.roll)
                    nav_data['pitch'] = math.degrees(msg.pitch)
                    nav_data['yaw'] = math.degrees(msg.yaw)

                elif msg_type == 'VFR_HUD':
                    nav_data['groundspeed'] = msg.groundspeed

                elif msg_type == 'SYSTEM_TIME':
                    nav_data['boot_time_ms'] = msg.time_boot_ms
                    if msg.time_unix_usec > 0:
                        dt_object = datetime.fromtimestamp(msg.time_unix_usec / 1000000.0)
                        nav_data['unix_time_str'] = dt_object.strftime('%H:%M:%S')

                elif msg_type == 'GPS_RAW_INT':
                    nav_data['sats'] = msg.satellites_visible
                    nav_data['fix_type'] = msg.fix_type

                nav_data['last_update'] = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            # 4. Terminal Dashboard Rendering (Buffer-based to prevent flickering)
            output = []
            output.append("\033[H") # Move cursor to top-left
            output.append("="*45)
            output.append(f" CUBE PILOT NAVIGATION DATA (5Hz) ")
            output.append("="*45)
            output.append(f" Last Update:  {nav_data['last_update']}")
            output.append(f" Port:         {port} @ {baud}")
            output.append("-" * 45)
            output.append(f" SYSTEM TIME & GPS STATUS")
            output.append(f"  Boot Time:   {nav_data['boot_time_ms']:11d} ms")
            output.append(f"  Unix Time:   {nav_data['unix_time_str']:>11s}")
            output.append(f"  Sats:        {nav_data['sats']:11d}")
            output.append(f"  GPS Fix:     {nav_data['fix_type']:11d}")
            output.append("-" * 45)
            output.append(f" POSITION")
            output.append(f"  Latitude:    {nav_data['lat']:11.7f} deg")
            output.append(f"  Longitude:   {nav_data['lon']:11.7f} deg")
            output.append(f"  Alt (Rel):   {nav_data['alt']:11.2f} m")
            output.append("-" * 45)
            output.append(f" ATTITUDE")
            output.append(f"  Roll:        {nav_data['roll']:11.2f} deg")
            output.append(f"  Pitch:       {nav_data['pitch']:11.2f} deg")
            output.append(f"  Yaw/Heading: {nav_data['yaw']:11.2f} deg")
            output.append("-" * 45)
            output.append(f" HUD DATA")
            output.append(f"  Heading:     {nav_data['heading']:11.2f} deg")
            output.append(f"  Groundspeed: {nav_data['groundspeed']:11.2f} m/s")
            output.append("="*45)
            output.append(" Press Ctrl+C to exit")
            
            # Print the entire buffer at once
            sys.stdout.write("\n".join(output) + "\n")
            sys.stdout.flush()

            # Small delay to reduce CPU load while maintaining 5Hz responsiveness
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Verify COM port name in Device Manager.")
        print("2. Ensure no other apps (Mission Planner) are using the port.")
        print("3. Check TX/RX wiring if using a serial adapter.")

if __name__ == "__main__":
    main()
