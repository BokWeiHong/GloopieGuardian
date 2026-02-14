from gpiozero import MCP3008, Button
from time import sleep

CLOCK_PIN = 21
MOSI_PIN = 20
MISO_PIN = 19
SELECT_PIN = 16

BUTTON_PIN = 26

try:
    print("--- DIAGNOSTIC MODE ---")

    joystick_x = MCP3008(channel=0, clock_pin=CLOCK_PIN, mosi_pin=MOSI_PIN, miso_pin=MISO_PIN, select_pin=SELECT_PIN)
    joystick_y = MCP3008(channel=1, clock_pin=CLOCK_PIN, mosi_pin=MOSI_PIN, miso_pin=MISO_PIN, select_pin=SELECT_PIN)

    joy_btn = Button(BUTTON_PIN)

    print(f"ADC Pins: CLK={CLOCK_PIN}, MOSI={MOSI_PIN}, MISO={MISO_PIN}, CS={SELECT_PIN}")
    print(f"Button Pin: GPIO {BUTTON_PIN}")
    print("Reading values... (Press Ctrl+C to stop)")

    while True:
        # Read Analog Values (0.0 to 1.0)
        x_val = joystick_x.value
        y_val = joystick_y.value
        
        # Read Digital Button (True/False)
        is_pressed = joy_btn.is_pressed
        btn_status = "PRESSED" if is_pressed else "Open"

        # Print all data in one line
        print(f"X: {x_val:.2f} | Y: {y_val:.2f} | Button: {btn_status}")
        
        sleep(0.2)

except Exception as e:
    print(f"Error: {e}")
except KeyboardInterrupt:
    print("\nExiting...")