import network
import uasyncio as asyncio
from config_manager import get_config
from log_manager import log

sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
_wifi_lock = False

CONNECT_RETRIES = 5
RETRY_DELAY = 2
CHECK_INTERVAL = 300
INTERFACE_RESET_DELAY = 0.5

async def _disable_interfaces():
    sta.active(False)
    ap.active(False)
    await asyncio.sleep(INTERFACE_RESET_DELAY)

def wifi_config():
    return get_config().get('wifi', {})

async def sync_time(retries=5):
    import ntptime
    ntptime.timeout = 3
    ntptime.host = 'time.google.com'
    for i in range(retries):
        try:
            ntptime.settime()
            return True
        except Exception:
            await asyncio.sleep(RETRY_DELAY)
    return False

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
        await asyncio.sleep(0.5)
        sta.connect(wifi['ssid'], wifi['password'])
        for _ in range(CONNECT_RETRIES):
            if sta.isconnected(): break
            status = sta.status()
            if status in (network.STAT_WRONG_PASSWORD, network.STAT_NO_AP_FOUND, network.STAT_CONNECT_FAIL):
                log(f'ERROR | Wi-Fi failed, status: {status}')
                return False
            await asyncio.sleep(RETRY_DELAY)
        else:
            log('ERROR | Wi-Fi connection timeout')
            return False
        await asyncio.sleep(1)
        await sync_time()
        if all(k in wifi for k in ('ip', 'mask', 'dns', 'gw')):
            sta.ifconfig((wifi['ip'], wifi['mask'], wifi['gw'], wifi['dns']))
        return True
    except Exception as e:
        log(f'ERROR | Wi-Fi exception: {e}')
        return False
    finally:
        _wifi_lock = False

async def start_ap(ssid='PicoW'):
    await _disable_interfaces()
    ap.active(True)
    await asyncio.sleep(0.5)
    ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))
    ap.config(essid=ssid, security=0)  # Open network
    while not ap.active():
        await asyncio.sleep(0.1)


async def keep_wifi():
    while True:
        try:
            if not sta.isconnected():
                if not await connect_to_wifi():
                    log("ERROR | Reconnect failed, starting AP")
                    await start_ap()
        except Exception as e:
            log(f'ERROR | Wi-Fi loop error: {str(e)}')
        await asyncio.sleep(CHECK_INTERVAL)
