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

        time.sleep(5)
    except Exception as e:
        print(f"Failed to start OpenRGB server: {e}")


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


def apply_rgb_color_cpu(red, green, blue, prev_rgb):
    """
    Apply RGB color to ASUS Aura LED Controller if it differs from the current color.
    """
    if (red, green, blue) == prev_rgb:
        return prev_rgb

    hex_color = f"{red:02x}{green:02x}{blue:02x}"
    try:
        subprocess.run(
            [
                "liquidctl",
                "--device",
                "0",
                "set",
                "sync",
                "color",
                "static",
                hex_color,
            ],
            check=True,
        )
        print(f"Aura RGB set to R={red}, G={green}, B={blue} (#{hex_color})")
    except subprocess.CalledProcessError as e:
        print(f"Error setting Aura RGB color: {e}")
    return red, green, blue


def apply_rgb_color_mouse(client: OpenRGBClient, red, green, blue, prev_rgb):
    """
    Apply RGB color to G02 Gaming HERO Mouse if it differs from the current color.

    Returns:
        tuple: Updated RGB values.
    """
    if (red, green, blue) == prev_rgb:
        return prev_rgb

    rgb_color = RGBColor(red, green, blue)

    for device in client.devices:
        print(f"Targeting device: {device.name}")
        try:
            if "G502" in device.name:  # Handle Logitech mouse
                if "Static" in [mode.name for mode in device.modes]:
                    device.set_mode("Static")
                    device.set_color(rgb_color)
                    print(f"{device.name} RGB set to R={red}, G={green}, B={blue}")
                else:
                    print(f"Static mode not available for {device.name}")

        except Exception as e:
            print(f"Error applying color to {device.name}: {e}")
    return red, green, blue


if __name__ == "__main__":
    prev_aura_rgb = (-1, -1, -1)  # Track previous Aura RGB color
    prev_mouse_rgb = (-1, -1, -1)  # Track previous mouse RGB color
    start_openrgb_server()
    client = OpenRGBClient(address="127.0.0.1", port=6742)
    for device in client.devices:
        print(f"Device Name: {device.name}")
        print(f"Device Type: {device.type}")
        print(f"Modes: {device.modes}")

    print(client.get_devices_by_type(DeviceType.COOLER))
    motherboard = client.get_devices_by_type(DeviceType.MOTHERBOARD)[0]
    print(client.get_devices_by_type(DeviceType.MOUSE))

    motherboard.colors[0] = RGBColor(255, 0, 0)
    print(motherboard.colors)
    client.show()

    while True:
        cpu_temp = get_cpu_temperature()
        if cpu_temp is not None:
            print(f"CPU Temperature: {cpu_temp}°C")
            red, green, blue = temperature_to_rgb(cpu_temp)
            prev_aura_rgb = apply_rgb_color_cpu(red, green, blue, prev_aura_rgb)
            prev_mouse_rgb = apply_rgb_color_mouse(
                client, red, green, blue, prev_mouse_rgb
            )
        else:
            print("Unable to read CPU temperature.")
        time.sleep(2)  # Adjust the interval as needed
