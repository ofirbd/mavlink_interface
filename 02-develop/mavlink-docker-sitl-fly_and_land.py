from pymavlink import mavutil
import time

# 1. Connect to SITL
connection = mavutil.mavlink_connection('tcp:127.0.0.1:5760')
connection.wait_heartbeat()
print(f"Connected to System {connection.target_system}")

# 2. Request Data Stream (10Hz)
connection.mav.request_data_stream_send(
    connection.target_system, connection.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)

def set_mode(mode):
    if mode not in connection.mode_mapping():
        print(f"Unknown mode: {mode}")
        return
    mode_id = connection.mode_mapping()[mode]
    connection.mav.set_mode_send(
        connection.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)
    print(f"Set Mode: {mode}")

def arm_and_takeoff(target_alt):
    # Plane needs GUIDED for takeoff via MAVLink
    set_mode('GUIDED')
    time.sleep(1)

    print("Arming motors...")
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0, 1, 0, 0, 0, 0, 0, 0)
    
    connection.motors_armed_wait()
    print("Armed!")

    print(f"Taking off to {target_alt}m...")
    # Param 7 is altitude for MAV_CMD_NAV_TAKEOFF
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0, 0, 0, 0, 0, 0, 0, target_alt)

def monitor_cycle(target_alt):
    # STATE 1: Climbing
    print("--- Phase: Climbing ---")
    while True:
        msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        curr_alt = msg.relative_alt / 1000.0
        print(f"Altitude: {curr_alt:.2f}m", end='\r')
        
        if curr_alt >= (target_alt * 0.95):
            print(f"\nTarget {target_alt}m reached!")
            break
    
    # STATE 2: Landing
    print("--- Phase: Landing ---")
    set_mode('LAND')
    
    while True:
        msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
        curr_alt = msg.relative_alt / 1000.0
        print(f"Landing... Altitude: {curr_alt:.2f}m", end='\r')
        
        # Check if we are close to the ground
        if curr_alt < 0.3:
            print("\nTouchdown detected!")
            break
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        arm_and_takeoff(50)
        monitor_cycle(50)
        print("Mission Complete. Vehicle is on the ground.")
    except KeyboardInterrupt:
        print("\nManual override.")