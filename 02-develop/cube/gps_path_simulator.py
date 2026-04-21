import time
import sys
import math
import datetime
from pymavlink import mavutil

def simulate_circular_path(connection_str, baud, center_lat, center_lon, alt, radius_m, velocity_ms):
    print(f"--- MAVLink GPS Path Simulator ---")
    print(f"Connecting to: {connection_str}")
    
    # mavutil.mavlink_connection handles both 'COMx' and 'udp:ip:port'
    connection = mavutil.mavlink_connection(connection_str, baud=baud)
    
    # Wait for heartbeat
    print("Waiting for heartbeat (Ensure Mission Planner Mirror is active)...")
    connection.wait_heartbeat(timeout=10)
    print("System Online. Starting Circular Simulation...")
    print(f"Radius: {radius_m}m | Speed: {velocity_ms}m/s")

    UPDATE_RATE_HZ = 5.0
    DT = 1.0 / UPDATE_RATE_HZ
    omega = velocity_ms / radius_m
    current_theta = 0.0

    lat_m_per_deg = 111319.5
    lon_m_per_deg = lat_m_per_deg * math.cos(math.radians(center_lat))

    try:
        while True:
            # 1. Update Position
            offset_north = radius_m * math.cos(current_theta)
            offset_east = radius_m * math.sin(current_theta)
            
            curr_lat = center_lat + (offset_north / lat_m_per_deg)
            curr_lon = center_lon + (offset_east / lon_m_per_deg)
            
            # 2. Calculate Velocity
            vn = -velocity_ms * math.sin(current_theta)
            ve = velocity_ms * math.cos(current_theta)
            vd = 0.0

            # 3. Calculate GPS Time from System Clock
            gps_epoch = datetime.datetime(1980, 1, 6, tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            delta = now - gps_epoch
            gps_week = delta.days // 7
            gps_tow_ms = int((delta.days % 7 * 24 * 3600 + delta.seconds) * 1000 + delta.microseconds / 1000)

            lat_int = int(curr_lat * 1e7)
            lon_int = int(curr_lon * 1e7)
            
            # 4. Send GPS_INPUT (ID #232)
            connection.mav.gps_input_send(
                0,                  # time_usec
                0,                  # gps_id
                0,                  # ignore_flags
                gps_tow_ms,         # time_week_ms
                gps_week,           # time_week
                3,                  # fix_type
                lat_int, lon_int, alt,
                1.0, 1.0, vn, ve, vd,
                0.1, 0.1, 0.1, 12
            )

            current_theta += (omega * DT)
            print(f"Pos: {curr_lat:.6f}, {curr_lon:.6f} | Brng: {math.degrees(current_theta)%360:.1f}°", end='\r')
            time.sleep(DT)

    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    # Default to UDP Mirror if no arguments provided
    conn_str = sys.argv[1] if len(sys.argv) > 1 else 'udp:127.0.0.1:14550'
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
    
    simulate_circular_path(
        connection_str=conn_str, 
        baud=baud, 
        center_lat=32.0853, 
        center_lon=34.7818, 
        alt=50.0, 
        radius_m=1000.0, 
        velocity_ms=20.0
    )
