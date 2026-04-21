import network
import time
import uasyncio as asyncio
from config_manager import get_config
from log_manager import log

sta = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)

def connect_to_wifi():
    sta.active(False)
    ap.active(False)
    time.sleep(1)

    conf = get_config()
    wifi = conf.get('wifi', {})
    if not wifi or not wifi.get('ssid'):
        log("ERROR | No Wi-Fi config found")
        return False
    
    sta.active(True)
    sta.connect(wifi['ssid'], wifi['password'])
    sta.ifconfig((wifi['ip'], wifi['mask'], wifi['gw'], wifi['dns']))
    log(f"NETWORK | Attempting to connect to {wifi['ssid']}")
    
    
    for _ in range(100):
        if sta.isconnected():
            print(sta.ifconfig())
            log(f"NETWORK | Connected: {sta.ifconfig()}")
            return True
        time.sleep(0.5)
    log("ERROR | Failed to connect to wifi")
    return False


def start_ap():
    sta.active(False)
    ap.active(False)
    time.sleep(1)
    ap.active(True)
    ap.config(essid='PicoW', password='12345678')
    log("NETWORK | Started AP")


async def keep_wifi(initial_fail=False):
    while True:
        if not sta.isconnected() and not ap.active():
            connected = connect_to_wifi()
            if not connected:
                log("ERROR | Failed to reconnect to network") 
                print("Reconnect Failed")
        await asyncio.sleep(10)
