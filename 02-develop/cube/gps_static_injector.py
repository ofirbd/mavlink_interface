import time
import sys
from pymavlink import mavutil

def inject_gps(connection_str, baud, lat, lon, alt):
    print(f"--- MAVLink GPS Injector ---")
    print(f"Connecting to: {connection_str}")
    
    # mavutil.mavlink_connection handles both 'COMx' and 'udp:ip:port'
    connection = mavutil.mavlink_connection(connection_str, baud=baud)
    
    # Wait for heartbeat to ensure connection
    print("Waiting for heartbeat (Ensure Mission Planner Mirror is active)...")
    connection.wait_heartbeat(timeout=10)
    print("System Online. Starting GPS Injection...")

    # Constants for GPS_INPUT message
    GPS_FIX_TYPE_3D = 3
    SATELLITES_VISIBLE = 10
    
    # Coordinates in MAVLink format (degrees * 1e7)
    lat_int = int(lat * 1e7)
    lon_int = int(lon * 1e7)
    
    start_time = time.time()

    try:
        while True:
            # Calculate GPS Time from System Clock
            import datetime
            gps_epoch = datetime.datetime(1980, 1, 6, tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            delta = now - gps_epoch
            gps_week = delta.days // 7
            gps_tow_ms = int((delta.days % 7 * 24 * 3600 + delta.seconds) * 1000 + delta.microseconds / 1000)

            # Send GPS_INPUT (ID #232)
            connection.mav.gps_input_send(
                0,                  # time_usec
                0,                  # gps_id
                0,                  # ignore_flags
                gps_tow_ms,         # time_week_ms
                gps_week,           # time_week
                GPS_FIX_TYPE_3D,    # fix_type
                lat_int,            # lat
                lon_int,            # lon
                alt,                # alt (meters)
                1.0,                # hdop
                1.0,                # vdop
                0, 0, 0,            # velocity North, East, Down
                0.1,                # speed_accuracy
                0.1,                # horiz_accuracy
                0.1,                # vert_accuracy
                SATELLITES_VISIBLE  # satellites_visible
            )
            
            print(f"Injecting: {lat}, {lon} @ {alt}m", end='\r')
            time.sleep(0.2) # 5Hz

    except KeyboardInterrupt:
        print("\nStopping GPS injection.")

if __name__ == "__main__":
    # Default to UDP Mirror if no arguments provided
    # Usage: python script.py udp:127.0.0.1:14550 115200 32.0853 34.7818 10.0
    conn_str = sys.argv[1] if len(sys.argv) > 1 else 'udp:127.0.0.1:14550'
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
    
    target_lat = float(sys.argv[3]) if len(sys.argv) > 3 else 32.0853
    target_lon = float(sys.argv[4]) if len(sys.argv) > 4 else 34.7818
    target_alt = float(sys.argv[5]) if len(sys.argv) > 5 else 10.0
    
    inject_gps(conn_str, baud, target_lat, target_lon, target_alt)
