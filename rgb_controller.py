import time
import subprocess
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor, DeviceType


def start_openrgb_server():
    try:
        subprocess.Popen(
            ["./openRGB.AppImage", "--server"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("Starting OpenRGB server...")

        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                OpenRGBClient(address="127.0.0.1", port=6742)
                print(f"OpenRGB server started successfully after {attempt+1} attempts")
                return True
            except Exception:
                print(f"Waiting for server to start (attempt {attempt+1}/{max_attempts})...")
                time.sleep(1)
        
        print("Failed to connect to OpenRGB server after maximum attempts")
        return False
    except Exception as e:
        print(f"Failed to start OpenRGB server: {e}")
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
        print(f"Error reading sensors: {e}")
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
            print(f"No devices of type {device_type} found")
            return prev_rgb

    for device in target_devices:
        print(f"Targeting device: {device.name}")
        try:
            available_modes = [mode.name for mode in device.modes]
            if "Static" in available_modes:
                device.set_mode("Static")
                device.set_color(rgb_color)
                print(f"{device.name} RGB set to R={red}, G={green}, B={blue}")
            else:
                print(f"Static mode not available for {device.name}. Available modes: {available_modes}")

        except Exception as e:
            print(f"Error applying color to {device.name}: {e}")
    
    return (red, green, blue)


if __name__ == "__main__":
    prev_rgb = (-1, -1, -1) 
    
    if not start_openrgb_server():
        print("Failed to start OpenRGB server. Exiting.")
        exit(1)
    
    try:
        client = OpenRGBClient(address="127.0.0.1", port=6742)
        
        print("\nDetected devices:")
        for device in client.devices:
            print(f"Device: {device.name} (Type: {device.type})")
            print(f"  Available modes: {[mode.name for mode in device.modes]}")
            print(f"  Zones: {len(device.zones)}")
            print(f"  LEDs: {len(device.leds)}")
            print()
        
        while True:
            try:
                cpu_temp = get_cpu_temperature()
                if cpu_temp is not None:
                    print(f"CPU Temperature: {cpu_temp}°C")
                    red, green, blue = temperature_to_rgb(cpu_temp)
                    prev_rgb = apply_rgb_color(client, red, green, blue, prev_rgb)
                else:
                    print("Unable to read CPU temperature.")
            except Exception as e:
                print(f"Error in main loop: {e}")
            
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nExiting RGB controller...")
    except Exception as e:
        print(f"Fatal error: {e}")
