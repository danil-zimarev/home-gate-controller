import uasyncio as asyncio
import time

from network_manager import connect_to_wifi, start_ap, keep_wifi
from pin_manager import init_pins, toggle_pin
from log_manager import log_network_state, periodic_cleanup, log
from web_server import app


BOOT_MS = time.ticks_ms()

def uptime_ms():
    return time.ticks_diff(time.ticks_ms(), BOOT_MS)

async def start_web():
    await app.run(port=80, debug=False)

async def wifi_boot():
    if not await connect_to_wifi():
        await start_ap()

async def startup_sequence():
    start = uptime_ms()
    init_pins()
    toggle_pin('LED')
    await wifi_boot()
    log(f'SYSTEM | Boot sequence finished in {uptime_ms() - start}ms')

async def main():
    await startup_sequence()
    await asyncio.gather(
        start_web(),
        keep_wifi(),
        log_network_state(),
        periodic_cleanup()
    )   
    
try:
    asyncio.run(main())
except KeyboardInterrupt:
    log('SYSTEM | Shutdown requested by user')
