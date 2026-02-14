import sys
import os
import socket
import subprocess 
from waveshare_epd import epd2in13_V4
from PIL import Image, ImageDraw, ImageFont
import time
from datetime import datetime

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


def show_sleep_image(epd, pause=2):
    try:
        epd.Clear(0xFF)

        canvas = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas)

        try:
            sleep_img = Image.open('img/sleeping.png').convert('RGBA')
            sleep_img = sleep_img.resize((150, 80), resample=Image.NEAREST)
            canvas.paste(sleep_img, (40, 40), mask=sleep_img)

            draw.text((70, 10), "--- SYSTEM OFF ---", font=font, fill=0)
            draw.text((100, 20), "GG out ~~", font=font, fill=0)
        except IOError:
            print("Sleep image 'img/sleeping.png' not found. Showing text only.")
            draw.text((70, 10), "--- SYSTEM OFF ---", font=font, fill=0)
            draw.text((100, 25), "GG out ~~", font=font, fill=0)

        epd.display(epd.getbuffer(canvas.rotate(90, expand=True)))
        time.sleep(pause)
        print("Sleep image displayed (left visible).")

    except Exception as e:
        print(f"Error showing sleep image: {e}")
        try:
            epd.Clear(0xFF)
        except Exception:
            pass


try:
    epd = epd2in13_V4.EPD()
    
    try:
        font = ImageFont.truetype('/home/pi/GloopieGuardian/static/fonts/PressStart2P-Regular.ttf', 6)
    except IOError:
        print("Custom font not found. Using default.")
        font = ImageFont.load_default()

    try:
        img_raw = Image.open('img/gg.png').convert('RGBA')
        img_raw = img_raw.resize((100, 75), resample=Image.NEAREST)
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
    print("\nExiting and showing sleeping image...")
    try:
        show_sleep_image(epd)
    except Exception as e:
        print(f"Error during exit: {e}")

    # Leave the image visible; exit without sleeping/module_exit
    print("Exiting now.")
    os._exit(0)
