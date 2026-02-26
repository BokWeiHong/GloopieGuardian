import os
import yaml
import subprocess
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET

def get_wireless_interface():
    try:
        interfaces = os.listdir('/sys/class/net/')
        wlan_ifaces = [iface for iface in interfaces if iface.startswith('wl')]
        
        if not wlan_ifaces:
            return None

        for iface in wlan_ifaces:
            if iface.endswith('mon'):
                return iface.replace('mon', '')

        if 'wlan1' in wlan_ifaces:
            return 'wlan1'
            
        return wlan_ifaces[0]
    except Exception:
        return None

# --- Views ---

@login_required
def tracker_view(request):
    return render(request, 'tracker/tracker.html')

@require_POST
@login_required
def start_network_scan(request):
    try:
        wifi_iface = get_wireless_interface()
        
        if not wifi_iface:
            return JsonResponse({
                'status': 'error', 
                'message': 'No wireless interface (wlan) found on the system.'
            }, status=400)

        systemctl_cmd = ['sudo', '/bin/systemctl', 'start', f'trackerjacker@{wifi_iface}.service']
        subprocess.run(systemctl_cmd, check=True, capture_output=True, text=True)

        return JsonResponse({
            'status': 'success', 
            'message': f'Scanner started successfully on {wifi_iface} in the background.'
        })

    except subprocess.CalledProcessError as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'Failed to start scanner service: {e.stderr}'
        }, status=500)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)


@require_GET
@login_required
def status_network_scan(request):
    try:
        wifi_iface = get_wireless_interface()

        if not wifi_iface:
            return JsonResponse({
                'status': 'inactive',
                'running': False
            })

        systemctl_cmd = ['/bin/systemctl', 'is-active', f'trackerjacker@{wifi_iface}.service']
        proc = subprocess.run(systemctl_cmd, check=False, capture_output=True, text=True)
        active = proc.stdout.strip() == 'active'

        if not active:
            systemctl_cmd2 = ['/bin/systemctl', 'is-active', 'trackerjacker.service']
            proc2 = subprocess.run(systemctl_cmd2, check=False, capture_output=True, text=True)
            active = proc2.stdout.strip() == 'active'

        return JsonResponse({
            'status': 'active' if active else 'inactive',
            'running': active
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'running': False,
            'message': str(e)
        }, status=500)

@require_POST
@login_required
def stop_network_scan(request):
    try:
        wifi_iface = get_wireless_interface()
        
        if not wifi_iface:
            return JsonResponse({
                'status': 'error', 
                'message': 'No wireless interface found to stop.'
            }, status=400)

        systemctl_cmd = ['sudo', '/bin/systemctl', 'stop', f'trackerjacker@{wifi_iface}.service']
        subprocess.run(systemctl_cmd, check=False, capture_output=True, text=True)

        is_active = subprocess.run(
            ['/bin/systemctl', 'is-active', f'trackerjacker@{wifi_iface}.service'],
            check=False, capture_output=True, text=True
        ).stdout.strip()

        if is_active == 'active':
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to stop scanner service on {wifi_iface}.'
            }, status=500)

        return JsonResponse({
            'status': 'success',
            'message': f'Scanner stopped and {wifi_iface} restored to normal mode.'
        })

    except subprocess.CalledProcessError as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'Failed to stop scanner service: {e.stderr}'
        }, status=500)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)

@login_required
@require_GET
def get_wifi_map_data(request):
    yaml_file_path = '/home/pi/GloopieGuardian/app/tracker/saves/wifi_map.yaml'

    if not os.path.exists(yaml_file_path):
        return JsonResponse({
            'status': 'waiting',
            'message': 'Scan has not generated data yet. Waiting for trackerjacker...'
        }, status=200)

    try:
        with open(yaml_file_path, 'r') as file:
            wifi_data = yaml.safe_load(file)

        return JsonResponse({
            'status': 'success',
            'data': wifi_data
        }, status=200)

    except yaml.YAMLError as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to parse YAML file: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)