import time
import subprocess
import os
import logging
from datetime import datetime
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/tmp/rgb_controller.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RGBController")

def start_openrgb_server():
    try:
        subprocess.Popen(
            ["./openRGB.AppImage", "--server"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("Starting OpenRGB server...")

        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                OpenRGBClient(address="127.0.0.1", port=6742)
                logger.info(f"OpenRGB server started successfully after {attempt+1} attempts")
                return True
            except Exception:
                logger.info(f"Waiting for server to start (attempt {attempt+1}/{max_attempts})...")
                time.sleep(1)
        
        logger.error("Failed to connect to OpenRGB server after maximum attempts")
        return False
    except Exception as e:
        logger.error(f"Failed to start OpenRGB server: {e}")
        return False

def get_rgb_client():
    """
    Create and return an OpenRGBClient instance.
    Handles connection errors and retries.
    """
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            client = OpenRGBClient(address="127.0.0.1", port=6742)
            return client
        except Exception as e:
            logger.warning(f"Connection attempt {attempt+1}/{max_attempts} failed: {e}")
            if attempt < max_attempts - 1:
                logger.info("Retrying in 5 seconds...")
                time.sleep(5)
    
    return None

def detect_sleep_wake(last_timestamp):
    """
    Detect if system has gone through sleep/wake cycle by checking time difference.
    Returns True if a sleep/wake cycle is detected, False otherwise.
    """
    current_time = datetime.now()
    time_diff = (current_time - last_timestamp).total_seconds()
    
    if time_diff > 30:
        logger.info(f"Sleep/wake cycle detected. Time gap: {time_diff:.2f} seconds")
        return True
    return False

def restart_openrgb_server():
    """
    Kill existing OpenRGB server process and start a new one.
    """
    try:
        subprocess.run(["pkill", "-f", "openRGB"], stderr=subprocess.DEVNULL)
        logger.info("Killed existing OpenRGB processes")
        time.sleep(1)
        
        return start_openrgb_server()
    except Exception as e:
        logger.error(f"Error restarting OpenRGB server: {e}")
        return False

def get_cpu_temperature():
    """
    Get the CPU temperature using the `sensors` command.
    Returns the temperature as a float, or None if unavailable.
    """
    try:
        result = subprocess.run(["sensors"], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if "Tctl" in line:
                temp = float(line.split()[1].replace("+", "").replace("°C", ""))
                return temp
    except Exception as e:
        logger.error(f"Error reading sensors: {e}")
    return None

def temperature_to_rgb(temp):
    """
    Map the input temperature to predefined color bands.
    """
    if temp <= 30:
        return 0, 0, 255  # Blue
    elif temp <= 40:
        return 63, 0, 192  # Purple-blue
    elif temp <= 45:
        return 0, 255, 0  # Green
    elif temp <= 50:
        return 127, 255, 0  # Green-yellow
    elif temp <= 60:
        return 255, 255, 0  # Yellow
    elif temp <= 65:
        return 255, 127, 0  # Orange-red
    else:
        return 255, 0, 0  # Red

def apply_rgb_color(client: OpenRGBClient, red, green, blue, prev_rgb, device_type=None):
    """
    Apply RGB color to devices of a specific type or all devices if type is None.
    
    Args:
        client: OpenRGBClient instance
        red, green, blue: RGB color values
        prev_rgb: Previous RGB values
        device_type: DeviceType to filter devices (optional)
        
    Returns:
        tuple: Updated RGB values.
    """
    if (red, green, blue) == prev_rgb:
        return prev_rgb

    rgb_color = RGBColor(red, green, blue)
    
    target_devices = client.devices
    if device_type is not None:
        target_devices = client.get_devices_by_type(device_type)
        if not target_devices:
            logger.warning(f"No devices of type {device_type} found")
            return prev_rgb

    for device in target_devices:
        logger.debug(f"Targeting device: {device.name}")
        try:
            available_modes = [mode.name for mode in device.modes]
            if "Static" in available_modes:
                device.set_mode("Static")
                device.set_color(rgb_color)
                logger.debug(f"{device.name} RGB set to R={red}, G={green}, B={blue}")
            else:
                logger.warning(f"Static mode not available for {device.name}. Available modes: {available_modes}")

        except Exception as e:
            logger.error(f"Error applying color to {device.name}: {e}")
    
    return (red, green, blue)

def print_device_info(client):
    """
    Print information about all detected devices.
    """
    logger.info("\nDetected devices:")
    for device in client.devices:
        logger.info(f"Device: {device.name} (Type: {device.type})")
        logger.info(f"  Available modes: {[mode.name for mode in device.modes]}")
        logger.info(f"  Zones: {len(device.zones)}")
        logger.info(f"  LEDs: {len(device.leds)}")
        logger.info("")

if __name__ == "__main__":
    logger.info("RGB Controller starting up...")
    prev_rgb = (-1, -1, -1)
    last_check_time = datetime.now()
    
    if not start_openrgb_server():
        logger.error("Failed to start OpenRGB server. Exiting.")
        exit(1)
    
    client = None
    
    while True:
        try:
            current_time = datetime.now()
            
            if detect_sleep_wake(last_check_time):
                logger.info("System appears to have woken from sleep. Reinitializing...")
                client = None
                restart_openrgb_server()
            
            last_check_time = current_time
            
            if client is None:
                client = get_rgb_client()
                if client is None:
                    logger.warning("Failed to connect to OpenRGB server. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                
                print_device_info(client)
            
            
            try:
                cpu_temp = get_cpu_temperature()
                if cpu_temp is not None:
                    logger.info(f"CPU Temperature: {cpu_temp}°C")
                    red, green, blue = temperature_to_rgb(cpu_temp)
                    
                    try:
                        prev_rgb = apply_rgb_color(client, red, green, blue, prev_rgb)
                    except Exception as e:
                        logger.error(f"Error applying RGB color: {e}")
                        client = None
                        continue
                else:
                    logger.warning("Unable to read CPU temperature.")
            except Exception as e:
                logger.error(f"Error in temperature processing: {e}")
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            logger.info("\nExiting RGB controller...")
            break
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}")
            logger.info("Resetting connection and retrying in 5 seconds...")
            client = None
            time.sleep(5)
