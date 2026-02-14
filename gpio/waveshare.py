import sys
import os
import socket
import subprocess 
from waveshare_epd import epd2in13_V4
from PIL import Image, ImageDraw, ImageFont
import time
from datetime import datetime

# --- Configuration ---
CUSTOM_WIDTH  = 100 
CUSTOM_HEIGHT = 75

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = 'No Internet'
    finally:
        s.close()
    return ip

def check_usb_status():
    try:
        output = subprocess.check_output("lsusb", shell=True).decode("utf-8")
        alfa = "MediaTek" in output or "Realtek" in output or "Atheros" in output
        gps  = "U-Blox" in output or "GNSS" in output or "GPS" in output
        return gps, alfa
    except Exception:
        return False, False

def get_system_state():
    """ Collect data to see if screen needs updating """
    ip = get_ip_address()
    gps, alfa = check_usb_status()
    time_str = datetime.now().strftime("%H:%M")
    return ip, gps, alfa, time_str

try:
    epd = epd2in13_V4.EPD()
    
    try:
        font = ImageFont.truetype('/home/pi/GloopieGuardian/static/fonts/PressStart2P-Regular.ttf', 6)
    except IOError:
        print("Custom font not found. Using default.")
        font = ImageFont.load_default()

    try:
        img_raw = Image.open('img/gg.png').convert('RGBA')
        img_raw = img_raw.resize((CUSTOM_WIDTH, CUSTOM_HEIGHT), resample=Image.NEAREST)
    except IOError:
        print("Image 'img/gg.png' not found. Skipping image.")
        img_raw = None

    print("Initializing screen...")
    epd.init()
    epd.Clear(0xFF)

    base_canvas = Image.new('1', (epd.height, epd.width), 255)
    draw_base = ImageDraw.Draw(base_canvas)

    if img_raw:
        base_canvas.paste(img_raw, (5, 25), mask=img_raw)
    
    draw_base.text((125, 25), "Hello, \nGloopie here!", font=font, fill=0)
    draw_base.text((5, 115), "GPS:", font=font, fill=0)
    draw_base.text((125, 115), "Alfa:", font=font, fill=0)
    draw_base.line((0, 15, epd.height, 15), fill=0, width=1)
    draw_base.line((0, 110, epd.height, 110), fill=0, width=1)

    epd.displayPartBaseImage(epd.getbuffer(base_canvas.rotate(90, expand=True)))

    print("System Monitor Running... (Partial Refresh Active)")
    last_state = None 

    while True:
        current_state = get_system_state()

        if current_state != last_state:
            ip, gps_ok, alfa_ok, time_str = current_state

            dynamic_canvas = base_canvas.copy()
            draw_dynamic = ImageDraw.Draw(dynamic_canvas)

            draw_dynamic.text((5, 5), f"IP:{ip}", font=font, fill=0)
            draw_dynamic.text((125, 5), f"Time:{time_str}", font=font, fill=0)

            if gps_ok:
                draw_dynamic.text((35, 115), "[OK]", font=font, fill=0)
            else:
                draw_dynamic.text((35, 115), "!ERR!", font=font, fill=0)

            if alfa_ok:
                draw_dynamic.text((160, 115), "[OK]", font=font, fill=0)
            else:
                draw_dynamic.text((160, 115), "!ERR!", font=font, fill=0)

            epd.displayPartial(epd.getbuffer(dynamic_canvas.rotate(90, expand=True)))
            
            last_state = current_state
            print(f"Screen updated at {time_str}")

        time.sleep(1)

except KeyboardInterrupt:    
    print("\nExiting and clearing screen...")
    epd.init()
    epd.Clear(0xFF) 
    epd.sleep()
    epd2in13_V4.EPD().module_exit()
    sys.exit()