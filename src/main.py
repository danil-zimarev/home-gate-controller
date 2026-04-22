import uasyncio as asyncio

from network_manager import connect_to_wifi, start_ap, keep_wifi
from pin_manager import init_pins, toggle_pin
from log_manager import log_network_state, log, periodic_cleanup
from web_server import app


async def start_web():
    await app.run(port=80, debug=True)

async def startup_sequence():
    log('SYSTEM | Boot sequence started')
    init_pins()
    toggle_pin('LED')
    if not await connect_to_wifi():
        await start_ap()
    log('SYSTEM | Boot sequence finished')

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
