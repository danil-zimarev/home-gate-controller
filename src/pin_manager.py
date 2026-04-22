from machine import Pin
from config_manager import get_config

PINS = {}

def init_pins():
    global PINS, PIN_STATES
    conf = get_config()
    pins_conf = conf.get('pins', {})

    for p_num, settings in pins_conf.items():
        if settings.get('enabled', False):
            pin_id = int(p_num) if p_num != 'LED' else p_num
            pin = Pin(pin_id, Pin.OUT)
            pin.on() if pin_id != 'LED' and pin_id < 16 else pin.off()
            PINS[p_num] = pin
    

def toggle_pin(pin_name):
    if pin_name not in PINS:
        return None
    PINS[pin_name].toggle()
    pin_value = PINS[pin_name].value()
    return not pin_value if pin_name.isdigit() and int(pin_name) < 16 else pin_value

