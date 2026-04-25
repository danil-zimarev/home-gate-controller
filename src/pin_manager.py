from machine import Pin
from config_manager import get_config

PINS = {}

def is_active_low(pin):
    return pin.isdigit() and int(pin) < 16


def init_pins():
    PINS.clear()
    pins = get_config().get('pins', {})

    for name, cfg in pins.items():
        if not cfg.get('enabled'):
            continue
        pin_id = name if name == 'LED' else int(name)
        pin = Pin(pin_id, Pin.OUT)
        pin.value(1 if is_active_low(name) else 0)
        PINS[name] = pin

def toggle_pin(name):
    pin = PINS.get(name)
    if not pin:
        return None
    pin.toggle()
    value = pin.value()
    return not value if is_active_low(name) else bool(value)
