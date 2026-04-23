import network
import uasyncio as asyncio
import ntptime
from config_manager import get_config
from log_manager import log
from microdot import auth

sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)

CONNECT_RETRIES = 20
RETRY_DELAY = 0.5
CHECK_INTERVAL = 10
INTERFACE_RESET_DELAY = 0.2

_wifi_lock = False

# ------------------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------------------

async def _disable_interfaces():
    sta.active(False)
    ap.active(False)
    await asyncio.sleep(INTERFACE_RESET_DELAY)

def wifi_config():
    return get_config().get('wifi', {})

async def sync_time(retries=5):
    ntptime.timeout = 3
    ntptime.host = 'time.google.com'
    for i in range(retries):
        try:
            ntptime.settime()
            return True
        except Exception as e:
            await asyncio.sleep(RETRY_DELAY)
    return False

# ------------------------------------------------------------------------------------------
# Wi-Fi logic
# ------------------------------------------------------------------------------------------

async def connect_to_wifi():
    global _wifi_lock
    if _wifi_lock:
        return sta.isconnected()

    _wifi_lock = True
    try:
        wifi = wifi_config()
        if not wifi.get('ssid'):
            log('ERROR | Wi-Fi config missing')
            return False

        await _disable_interfaces()

        sta.active(True)
        sta.connect(wifi['ssid'], wifi['password'])

        for _ in range(CONNECT_RETRIES):
            if sta.isconnected():
                break
            await asyncio.sleep(RETRY_DELAY)
        else:
            log('ERROR | Wi-Fi connection timeout')
            return False
        await sync_time()
        if all(k in wifi for k in ('ip', 'mask', 'dns', 'gw')):
            sta.ifconfig((wifi['ip'], wifi['mask'], wifi['gw'], wifi['dns']))

        return True
    finally:
        _wifi_lock = False

async def start_ap(ssid='PicoW', password=''):
    await _disable_interfaces()
    ap.active(True)
    ap.config(essid=ssid, password=password, authmode=auth.WPA2_PSK if password else auth.OPEN)

# ------------------------------------------------------------------------------------------
# Background tasks
# ------------------------------------------------------------------------------------------

async def keep_wifi():
    while True:
        try:
            if not sta.isconnected() and not ap.active():
                if not await connect_to_wifi():
                    log("ERROR | Reconnect failed, starting AP")
                    await start_ap()
        except Exception as e:
            log(f'ERROR | Wi-Fi loop error: {str(e)}')
        await asyncio.sleep(CHECK_INTERVAL)
