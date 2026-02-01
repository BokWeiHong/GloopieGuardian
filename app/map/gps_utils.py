import serial
import pynmea2
import time
import glob
import subprocess
from threading import Lock

class GPSReader:
    def __init__(self, baudrate=9600, timeout=1):
        self.baudrate = baudrate
        self.timeout = timeout
        self._lock = Lock()
        self._last_position = None
        self._last_wifi = None
        self.ser = None
        self.port = None

    def find_port(self):
        ports = glob.glob("/dev/ttyACM*")
        return ports[0] if ports else None

    def connect(self):
        if self.ser:
            return True

        self.port = self.find_port()
        if not self.port:
            print("[GPS] No ttyACM device found")
            return False

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"[GPS] Connected to {self.port}")
            return True
        except Exception as e:
            print("[GPS] Failed to open port:", e)
            return False

    def read_line(self):
        try:
            if self.ser and self.ser.in_waiting:
                return self.ser.readline().decode("ascii", errors="ignore").strip()
        except Exception:
            pass
        return None

    def scan_wifi(self):
        try:
            output = subprocess.check_output(
                ["iw", "dev", "wlan0", "scan"],
                stderr=subprocess.DEVNULL
            ).decode()

            aps = []
            current = None

            for line in output.splitlines():
                if line.startswith("BSS"):
                    if current:
                        aps.append(current)
                    current = {"bssid": line.split()[1]}
                elif "signal:" in line and current:
                    current["signal"] = float(line.split()[1])

            if current:
                aps.append(current)

            return aps
        except Exception:
            return None

    def wifi_movement(self, old, new):
        if not old or not new:
            return 999

        old_map = {ap["bssid"]: ap["signal"] for ap in old}
        new_map = {ap["bssid"]: ap["signal"] for ap in new}

        score = 0
        for bssid in old_map:
            if bssid in new_map:
                score += abs(new_map[bssid] - old_map[bssid])

        return score

    def get_position(self, samples=8, max_time=5):
        if not self.connect():
            return self._last_position

        lat_list = []
        lon_list = []
        start = time.time()

        with self._lock:
            while time.time() - start < max_time:
                line = self.read_line()
                if not line or "GGA" not in line:
                    continue

                try:
                    msg = pynmea2.parse(line)

                    gps_qual = int(msg.gps_qual or 0)
                    num_sats = int(msg.num_sats or 0)

                    if gps_qual > 0 and num_sats >= 5:
                        lat_list.append(msg.latitude)
                        lon_list.append(msg.longitude)

                        if len(lat_list) >= samples:
                            break
                except pynmea2.ParseError:
                    continue

        # GOOD GPS FIX
        if len(lat_list) >= 3:
            lat = sum(lat_list) / len(lat_list)
            lon = sum(lon_list) / len(lon_list)

            pos = {
                "lat": round(lat, 7),
                "lon": round(lon, 7),
                "satellites": len(lat_list),
                "fix_quality": 1,
                "source": "gps_avg"
            }

            self._last_position = pos
            self._last_wifi = self.scan_wifi()
            return pos

        # NO GPS → WIFI HOLD
        wifi_now = self.scan_wifi()
        movement = self.wifi_movement(self._last_wifi, wifi_now)

        if self._last_position and movement < 15:
            return {
                **self._last_position,
                "source": "wifi_hold",
                "confidence": "low"
            }

        return self._last_position

gps_reader = GPSReader()
