import requests
import getpass

WIGLE_BASE_URL = "https://api.wigle.net/api/v2/network/search"

_cached_creds = None

def get_wigle_credentials():
    """Ask user for WiGLE credentials (not stored)."""
    global _cached_creds
    if _cached_creds:
        return _cached_creds

    user = input().strip()
    pw = getpass.getpass().strip()

    _cached_creds = (user, pw)
    return _cached_creds


def fetch_wigle_data(bssid):
    """Query WiGLE API for a specific BSSID (MAC)."""
    user, pw = get_wigle_credentials()

    try:
        response = requests.get(
            WIGLE_BASE_URL,
            auth=(user, pw),
            params={"netid": bssid},
            timeout=10
        )

        if response.status_code != 200:
            print(f"[!] WiGLE returned HTTP {response.status_code} for {bssid}")
            return None

        data = response.json()
        results = data.get("results", [])
        if not results:
            print(f"[-] No WiGLE data found for {bssid}")
            return None

        result = results[0]

        return {
            "bssid": bssid,
            "ssid": result.get("ssid"),
            "lat": result.get("trilat"),
            "lon": result.get("trilon"),
            "encryption": result.get("encryption"),
            "first_seen": result.get("firsttime"),
            "last_seen": result.get("lasttime"),
        }

    except requests.exceptions.Timeout:
        print("[!] WiGLE request timed out.")
    except Exception as e:
        print(f"[x] WiGLE lookup error for {bssid}: {e}")

    return None


def enrich_with_wigle_data(device):
    if not device.devmac:
        return None

    bssid = device.devmac.upper()
    data = fetch_wigle_data(bssid)
    if not data:
        return None

    device.wigle_data = data

    return data
