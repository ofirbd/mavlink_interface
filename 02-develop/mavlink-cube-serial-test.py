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
        # The 'serial:' prefix tells mavutil to use the serial backend
        connection = mavutil.mavlink_connection(port, baud=baud)

        # 2. Wait for the first heartbeat
        print("Waiting for Heartbeat from Cube...")
        connection.wait_heartbeat(timeout=10)
        print(f"Heartbeat received! System ID: {connection.target_system}, Component ID: {connection.target_component}")

        # Note: Since the Cube is configured to output automatically at 5Hz, 
        # we don't necessarily need to send request_data_stream, 
        # but it doesn't hurt to ensure it's active.
        connection.mav.request_data_stream_send(
            connection.target_system, connection.target_component,
            mavutil.mavlink.MAV_DATA_STREAM_ALL, 5, 1)

        # 3. Data Loop
        # Internal state to store latest values
        nav_data = {
            'lat': 0.0, 'lon': 0.0, 'alt': 0.0,
            'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
            'heading': 0, 'groundspeed': 0.0,
            'last_update': 'N/A'
        }

        while True:
            # Check for specific navigation messages
            # We use a short timeout to keep the loop responsive
            msg = connection.recv_match(type=['GLOBAL_POSITION_INT', 'ATTITUDE', 'VFR_HUD'], blocking=True, timeout=0.1)
            
            if msg:
                msg_type = msg.get_type()
                
                if msg_type == 'GLOBAL_POSITION_INT':
                    nav_data['lat'] = msg.lat / 1e7
                    nav_data['lon'] = msg.lon / 1e7
                    nav_data['alt'] = msg.relative_alt / 1000.0 # Relative Alt in meters
                
                elif msg_type == 'ATTITUDE':
                    import math
                    # Convert radians to degrees
                    nav_data['roll'] = math.degrees(msg.roll)
                    nav_data['pitch'] = math.degrees(msg.pitch)
                    nav_data['yaw'] = math.degrees(msg.yaw)

                elif msg_type == 'VFR_HUD':
                    nav_data['heading'] = msg.heading
                    nav_data['groundspeed'] = msg.groundspeed

                nav_data['last_update'] = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            # 4. Terminal Dashboard Rendering
            # Clear screen (cross-platform)
            # os.system('cls' if os.name == 'nt' else 'clear')
            
            # Print Dashboard
            print("\033[H", end="") # Move cursor to top-left (ANSI)
            print("="*45)
            print(f" CUBE PILOT NAVIGATION DATA (5Hz) ")
            print("="*45)
            print(f" Last Update:  {nav_data['last_update']}")
            print(f" Port:         {port} @ {baud}")
            print("-" * 45)
            print(f" POSITION")
            print(f"  Latitude:    {nav_data['lat']:11.7f} deg")
            print(f"  Longitude:   {nav_data['lon']:11.7f} deg")
            print(f"  Alt (Rel):   {nav_data['alt']:11.2f} m")
            print("-" * 45)
            print(f" ATTITUDE")
            print(f"  Roll:        {nav_data['roll']:11.2f} deg")
            print(f"  Pitch:       {nav_data['pitch']:11.2f} deg")
            print(f"  Yaw/Heading: {nav_data['yaw']:11.2f} deg")
            print("-" * 45)
            print(f" HUD DATA")
            print(f"  Heading:     {nav_data['heading']:11d} deg")
            print(f"  Groundspeed: {nav_data['groundspeed']:11.2f} m/s")
            print("="*45)
            print(" Press Ctrl+C to exit")

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
