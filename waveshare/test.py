import sys
import os
import socket
import subprocess 
from waveshare_epd import epd2in13b_V4
from PIL import Image, ImageDraw, ImageFont
import time
from datetime import datetime

# --- Configuration ---
CUSTOM_WIDTH  = 105   
CUSTOM_HEIGHT = 80

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

# --- DISPLAY FUNCTION ---
def update_display(epd, font, img_raw, state):
    ip, gps_ok, alfa_ok, time_str = state
    
    print(f"Refreshing screen for {time_str}...")
    epd.init()

    canvas_black = Image.new('1', (epd.height, epd.width), 255)
    canvas_red   = Image.new('1', (epd.height, epd.width), 255)
    
    draw_black   = ImageDraw.Draw(canvas_black)

    if img_raw:
        canvas_black.paste(img_raw, (5, 20), mask=img_raw)

    draw_black.text((5, 5), f"IP:{ip}", font=font, fill=0)
    draw_black.text((125, 5), f"Time:{time_str}", font=font, fill=0)

    draw_black.text((125, 25), "Hello, \nGloopie here!", font=font, fill=0)
    
    draw_black.text((5, 115), "GPS:", font=font, fill=0)
    if gps_ok:
        draw_black.text((35, 115), "[OK]", font=font, fill=0)
    else:

        draw_black.text((35, 115), "!MISSING!", font=font, fill=0)

    draw_black.text((125, 115), "Alfa:", font=font, fill=0)
    if alfa_ok:
        draw_black.text((160, 115), "[OK]", font=font, fill=0)
    else:
        draw_black.text((160, 115), "!MISSING!", font=font, fill=0)

    draw_black.line((0, 15, epd.height, 15), fill=0, width=1)
    draw_black.line((0, 110, epd.height, 110), fill=0, width=1)

    epd.display(epd.getbuffer(canvas_black), epd.getbuffer(canvas_red))
    epd.sleep()

try:
    epd = epd2in13b_V4.EPD()

    try:
        font = ImageFont.truetype('/home/pi/GloopieGuardian/static/fonts/PressStart2P-Regular.ttf', 6)
    except IOError:
        font = ImageFont.load_default()

    try:
        img_raw = Image.open('img/gg.png').convert('RGBA')
        img_raw = img_raw.resize((CUSTOM_WIDTH, CUSTOM_HEIGHT), resample=Image.NEAREST)
    except IOError:
        img_raw = None

    print("System Monitor Running... (Black & White Mode)")
    
    last_state = None 

    while True:
        current_state = get_system_state()

        if current_state != last_state:
            update_display(epd, font, img_raw, current_state)
            last_state = current_state
        
        time.sleep(1)

except KeyboardInterrupt:    
    epd2in13b_V4.EPD().module_exit()
    exit()