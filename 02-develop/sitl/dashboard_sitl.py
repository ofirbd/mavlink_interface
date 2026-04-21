from pymavlink import mavutil
import time
import os
from datetime import datetime

# Connect to Docker SITL (TCP)
connection = mavutil.mavlink_connection('tcp:127.0.0.1:5760')

print("Connecting to SITL...")
connection.wait_heartbeat()
print(f"Connected! System ID: {connection.target_system}")

# Request data streams at 10Hz
connection.mav.request_data_stream_send(
    connection.target_system, connection.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)

def display_nav_data():
    # Variables to store data between message arrivals
    lat, lon, alt = 0.0, 0.0, 0.0
    heading = 0
    boot_time_ms = 0

    try:
        while True:
            # Check for messages
            msg = connection.recv_match(type=['GLOBAL_POSITION_INT', 'VFR_HUD'], blocking=True)
            
            if msg.get_type() == 'GLOBAL_POSITION_INT':
                lat = msg.lat / 1e7
                lon = msg.lon / 1e7
                alt = msg.relative_alt / 1000.0  # Meters
                boot_time_ms = msg.time_boot_ms   # Timestamp from ArduPilot
                
            elif msg.get_type() == 'VFR_HUD':
                heading = msg.heading # Degrees (0-360)

            # Clear terminal for a clean dashboard look
            # os.system('cls' if os.name == 'nt' else 'clear')
            
            # Get current Windows System Time
            sys_time = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            print("-" * 40)
            print(f" ArduPilot Navigation Dashboard")
            print("-" * 40)
            print(f" System Time:    {sys_time}")
            print(f" Boot Time (ms): {boot_time_ms}")
            print(f" Latitude:       {lat:.7f}")
            print(f" Longitude:      {lon:.7f}")
            print(f" Altitude (Rel): {alt:.2f} m")
            print(f" Heading:        {heading}°")
            print("-" * 40)
            
            # Small sleep to prevent high CPU usage
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nStopping navigation readout.")

if __name__ == "__main__":
    display_nav_data()