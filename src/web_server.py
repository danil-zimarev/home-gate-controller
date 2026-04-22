import ujson
import uasyncio as asyncio
import machine

from microdot import Microdot, Response
from config_manager import get_config, update_config
from pin_manager import init_pins, toggle_pin
from log_manager import log, get_logs


# ------------------------------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------------------------------

app = Microdot()
Response.default_content_type = 'text/html'

PIN_STATES = {str(p): False if p < 16 else True for p in range(28)}
PIN_STATES["LED"] = False


# ------------------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------------------

def json_response(data, status=200):
    return Response(ujson.dumps(data), status_code=status)

def render_template(path, context=None):
    context = context or {}
    try:
        with open(path) as f:
            html = f.read()
        for k, v in context.items():
            html = html.replace(f'{{{{{k}}}}}', str(v))
        return html
    except OSError:
        log(f"ERROR | Template {path} not found")
        return f"Template {path} not found"

def sorted_pins(pins):
    numeric = sorted((p for p in pins if p.isdigit()), key=int)
    other = [p for p in pins if not p.isdigit()]
    return numeric + other

# ------------------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------------------

@app.route('/')
def index(request):
    conf = get_config()
    wifi = conf.get('wifi', {})
    pins = conf.get('pins', {})
    pin_checkboxes = []
    pin_toggles = []

    for p in sorted_pins(pins):
        pin = str(p)
        data = pins[pin]
        enabled = data.get('enabled', False)
        pin_checkboxes.append(
            f'<label><input type="checkbox" name="{pin}" {"checked" if enabled else ""}/> GPIO {pin}</label><br>'
        )

        if enabled:
            state = PIN_STATES.get(pin, False)
            pin_toggles.append(
                f'''
                <a href="/toggle/{pin}" class="pin-toggle-link" data-pin="{pin}">
                    GPIO {pin} <span class="toggle-state" style="color:{'green' if state else 'red'}">{'ON' if state else 'OFF'}</span>
                </a>
                '''
            )

    html = render_template('www/index.html', {
        "ssid": wifi.get("ssid", ""),
        "password": wifi.get("password", ""),
        "ip": wifi.get("ip", ""),
        "mask": wifi.get("mask", ""),
        "dns": wifi.get("dns", ""),
        "gw": wifi.get("gw", ""),
        "pin_checkboxes": ''.join(pin_checkboxes),
        "pin_toggles": ''.join(pin_toggles)
    })
    return Response(html)


@app.post('/toggle/<pin>')
def toggle(request, pin):
    pins = get_config().get('pins', {})

    if pin not in pins:
        return json_response({'status': 'error', 'message': 'Invalid Pin'}, 400)

    state = toggle_pin(pin)
    PIN_STATES[pin] = state
    return json_response({'status': 'ok', 'pin': pin, 'state': state})


@app.post('/save_network')
def save_network(request):
    try:
        data = request.json or {}
        required = ('ssid', 'password', 'ip', 'mask', 'dns', 'gw')
        if not all(k in data for k in required):
            return json_response({'status': 'error', 'message': 'Missing required fields'}, 400)

        conf = get_config()
        conf['wifi'] = {k: data[k] for k in required}
        update_config(conf)
        log(f"INFO | Network settings saved: {data}")
        return json_response({'status': 'ok'})
    except Exception as e:
        log(f"ERROR | Failed to save network: {e}")
        return json_response({'status': 'error', 'message': str(e)}, 500)

@app.post('save_pins')
def save_pins(request):
    try:
        data = request.json or {}
        enabled = data.get('enabled_pins', {})
        if not isinstance(enabled, dict):
            return json_response({'status': 'error', 'message': 'Invalid data'}, 400)
        conf = get_config()
        pins = conf.get('pins', {})

        for pin, value in enabled.items():
            if pin in pins:
                pins[pin]['enabled'] = bool(value)

        update_config(conf)
        init_pins()
        log('INFO | Pin config updated')
        return json_response({'status': 'ok'})
    except Exception as e:
        log(f"ERROR | Failed to save pins: {e}")
        return json_response({'status': 'error', 'message': str(e)}, 500)


@app.get('logs')
def logs_endpoint(request):
    return json_response({get_logs()})

@app.get('reload')
def reload_pico(request):
    log("SYSTEM | Reload requested")
    asyncio.create_task(_delayed_reboot())
    return json_response({'status': 'ok', 'message': 'Rebooting...'})

# ------------------------------------------------------------------------------------------
# Background tasks
# ------------------------------------------------------------------------------------------

async def _delayed_reboot():
    await asyncio.sleep(1)
    log("SYSTEM | Performing reboot")
    machine.reset()
