from pymavlink import mavutil
import time

# Connect to Docker SITL
connection = mavutil.mavlink_connection('tcp:127.0.0.1:5760')
connection.wait_heartbeat()
print(f"Heartbeat from System {connection.target_system}")

# 1. Request Data Stream so we can see altitude
connection.mav.request_data_stream_send(
    connection.target_system, connection.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)

def set_mode(mode):
    # Get mode ID from name
    if mode not in connection.mode_mapping():
        print(f"Unknown mode : {mode}")
        return
    mode_id = connection.mode_mapping()[mode]
    connection.mav.set_mode_send(
        connection.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)
    print(f"Switching to {mode} mode")

def arm_vehicle():
    print("Arming...")
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0)
    # Wait for confirmation
    connection.motors_armed_wait()
    print("Armed!")

def takeoff(altitude):
    print(f"Taking off to {altitude}m...")
    # For ArduPlane, param1 is the pitch angle (0 for auto), param7 is altitude
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0, 0, 0, 0, 0, 0, 0, altitude)

if __name__ == "__main__":
    # ArduPlane requires GUIDED mode for computer control
    set_mode('GUIDED')
    time.sleep(1)
    
    arm_vehicle()
    takeoff(50)

    # Monitor altitude
    while True:
        msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        alt = msg.relative_alt / 1000.0
        print(f"Current Altitude: {alt:.2f}m", end='\r')
        if alt >= 45: # Reach 90% of target
            print("\nTarget altitude reached!")
            break


        