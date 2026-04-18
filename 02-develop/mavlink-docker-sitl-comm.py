from pymavlink import mavutil
import time

# 1. Establish connection to Docker SITL via TCP
# Docker maps 127.0.0.1:5760 to the container's ArduPilot port
connection = mavutil.mavlink_connection('tcp:127.0.0.1:5760')

# 2. Wait for the first heartbeat to confirm connection
print("Waiting for heartbeat...")
connection.wait_heartbeat()
print(f"Heartbeat from system {connection.target_system} component {connection.target_component}")

# CRITICAL: Tell SITL to start sending data
connection.mav.request_data_stream_send(
    connection.target_system, connection.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)

def get_navigation_data():
    while True:
        # Request specific messages
        msg = connection.recv_match(type=['ATTITUDE', 'GLOBAL_POSITION_INT'], blocking=True)
        
        if not msg:
            continue
            
        if msg.get_type() == 'ATTITUDE':
            print(f"\n[ATTITUDE] Roll: {msg.roll:.2f}, Pitch: {msg.pitch:.2f}, Yaw: {msg.yaw:.2f}")
            
        elif msg.get_type() == 'GLOBAL_POSITION_INT':
            # Lat/Lon are sent as integers (degrees * 10^7)
            lat = msg.lat / 1e7
            lon = msg.lon / 1e7
            alt = msg.relative_alt / 1000.0 # Relative altitude in meters
            print(f"[POSITION] Lat: {lat}, Lon: {lon}, Alt: {alt}m")

        time.sleep(0.1)

if __name__ == "__main__":
    try:
        get_navigation_data()
    except KeyboardInterrupt:
        print("Closing connection...")