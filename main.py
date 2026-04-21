import uasyncio as asyncio
from network_manager import connect_to_wifi, start_ap, keep_wifi
from pin_manager import init_pins, toggle_pin
from log_manager import log_network_state, log, periodic_cleanup
from web_server import app


async def start_app():
    await app.run(port=80, debug=True)
    
async def main():
    log("SYSTEM | System started")
    init_pins()
    wifi_connected = connect_to_wifi()
    if not wifi_connected:
        start_ap()
    
    toggle_pin('LED')
    await asyncio.gather(
        start_app(),
        keep_wifi(),
        log_network_state(),
        periodic_cleanup()
    )   
    
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
