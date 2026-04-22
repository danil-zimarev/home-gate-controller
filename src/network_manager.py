import network
import uasyncio as asyncio

from config_manager import get_config
from log_manager import log

sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)

CONNECT_RETRIES = 20
RETRY_DELAY = 0.5
CHECK_INTERVAL = 10
INTERFACE_RESET_DELAY = 1

# ------------------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------------------

async def _disable_interfaces():
    sta.active(False)
    ap.active(False)
    await asyncio.sleep(INTERFACE_RESET_DELAY)



def wifi_config():
    return get_config().get('wifi', {})

# ------------------------------------------------------------------------------------------
# Wi-Fi logic
# ------------------------------------------------------------------------------------------

async def connect_to_wifi():
    wifi = wifi_config()
    if not wifi.get('ssid'):
        log('ERROR | Wi-Fi config missing')
        return False

    await _disable_interfaces()
    sta.active(True)
    log(f'NETWORK | Connecting to: {wifi['ssid']}')
    sta.connect(wifi['ssid'], wifi['password'])
    if all(k in wifi for k in ('ip', 'mask', 'dns', 'gw')):
        sta.ifconfig((wifi['ip'], wifi['mask'], wifi['gw'], wifi['dns']))

    for _ in range(CONNECT_RETRIES):
        if sta.isconnected():
            log(f'NETWORK | Connected: {sta.ifconfig()}')
            print(f'NETWORK | Connected: {sta.ifconfig()}')
            return True
        await asyncio.sleep_ms(int(RETRY_DELAY * 1000))
    print('ERROR | Wi-Fi connection timeout')
    log('ERROR | Wi-Fi connection timeout')
    return False


async def start_ap(ssid='PicoW', password='1234578'):
    await _disable_interfaces()
    ap.active(True)
    ap.config(essid=ssid, password=password)
    log(f"NETWORK | Started AP ({ssid})")

# ------------------------------------------------------------------------------------------
# Background tasks
# ------------------------------------------------------------------------------------------

async def keep_wifi():
    while True:
        if not sta.isconnected() and not ap.active():
            if not await connect_to_wifi():
                log("ERROR | Reconnect failed, starting AP")
                await start_ap()
        await asyncio.sleep(CHECK_INTERVAL)
