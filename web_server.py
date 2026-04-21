import ujson
import uasyncio as asyncio
from microdot.microdot import Microdot, Response
from config_manager import get_config, update_config
from pin_manager import init_pins, toggle_pin
from log_manager import log, get_logs
import machine


app = Microdot()
Response.default_content_type = 'text/html'
PIN_STATES = {str(p): False if p < 16 else True for p in range(0, 28)}
PIN_STATES["LED"] = False

@app.route('/')
def index(request):
    conf = get_config()
    wifi = conf.get('wifi', {})
    pins_conf = conf.get('pins', {})
    
    pin_checkboxes = ''
    pin_toggles = ''
    sorted_keys = sorted([k for k in pins_conf if k.isdigit()], key=int) + [k for k in pins_conf if not k.isdigit()]
        
    for pin in sorted_keys:
        data = pins_conf[pin]
        checked = 'checked' if data.get('enabled', False) else ''
        pin_checkboxes += f'<label><input type="checkbox" name="{pin}" {checked}/> GPIO {pin}</label><br>'
        
        if data.get('enabled', False):
            state = 'ON' if PIN_STATES.get(pin, True) else 'OFF'
            color = 'green' if PIN_STATES.get(pin, True) else 'red'
            pin_toggles += f'''
                <a href="/toggle/{pin}" class="pin-toggle-link" data-pin="{pin}">
                GPIO {pin} <span class="toggle-state" style="color:{color}">{state}</span>
                </a>
            '''
    context = {
        "ssid": wifi.get("ssid", ""),
        "password": wifi.get("password", ""),
        "ip": wifi.get("ip", ""),
        "mask": wifi.get("mask", ""),
        "dns": wifi.get("dns", ""),
        "gw": wifi.get("gw", ""),
        "pin_checkboxes": pin_checkboxes,
        "pin_toggles": pin_toggles
    }
    
    html = render_template('www/index.html', context)
    return Response(html)


@app.post('/toggle/<pin>')
def toggle(request, pin):
    conf = get_config()
    pins = conf.get('pins', {})

    if pin not in pins:
        return Response(ujson.dumps({'status': 'error', 'message': 'Invalid Pin'}), status_code=400)
    
    new_state = toggle_pin(pin)
    PIN_STATES[pin] = not PIN_STATES[pin]
    return Response(ujson.dumps({'status': 'ok', 'pin': pin, 'state': new_state}))


@app.post('/save_network')
def save_network(request):
    try:
        data = request.json
        if not data:
            return Response(ujson.dumps({'status': 'error', 'message': 'No data received'}))
        
        required_fields = ['ssid', 'password', 'ip', 'mask', 'dns', 'gw']
        for field in required_fields:
            if field not in data:
                return Response(ujson.dumps({'status': 'error', 'message': f'Missing field: {field}'}))
        
        conf = get_config()
        conf['wifi'] = {
            'ssid': data['ssid'],
            'password': data['password'],
            'ip': data['ip'],
            'mask': data['mask'],
            'dns': data['dns'],
            'gw': data['gw']
        }
        
        update_config(conf)
        log(f"INFO | Network settings saved: {data}")
        return Response(ujson.dumps({'status': 'ok'}))
    except:
        log(f"ERROR | Failed to save network: {str(e)}")
        return Response(ujson.dumps({'status': 'error', 'message': str(e)}), status_code=500)

@app.post('save_pins')
def save_pins(request):
    try:
        data = request.json
        if not data or 'enabled_pins' not in data:
            return Response(ujson.dumps({'status': 'error', 'message': 'Invalid data'}))
        
        enabled_pins = data['enabled_pins']
        conf = get_config()
        pins = conf.get('pins', {})
        
        for pin, enabled in enabled_pins.items():
            if pin in pins:
                pins[pin]['enabled'] = bool(enabled)
        
        conf['pins'] = pins
        update_config(conf)
        init_pins()
        log('INFO | Pin configuration updated')
        
        return Response(ujson.dumps({'status': 'ok', 'pins': pins}))
    except:
        log(f"ERROR | Failed to save pins: {str(e)}")
        return Response(ujson.dumps({'status': 'error', 'message': str(e)}), status_code=500)
    

@app.get('logs')
def logs_endpoint(request):
    data = get_logs()
    return Response(ujson.dumps(data))

@app.get('reload')
def reload_pico(request):
    try:
        log("SYSTEM | Reload requested via web")
        response = {'status': 'ok', 'message': 'Rebooting...'}
        asyncio.create_task(_delayed_reboot())
        return Response(ujson.dumps(response))
    except Exception as e:
        return Response(ujson.dumps({'status': 'error', 'message': str(e)}))

async def _delayed_reboot():
    await asyncio.sleep(1)
    log("SYSTEM | Performing reboot")
    machine.reset()
    

def render_template(filename, context=None):
    context = context or {}
    try:
        with open(filename, 'r') as f:
            html = f.read()
        for key, value in context.items():
            html = html.replace(f'{{{{{key}}}}}', str(value))
        return html
    except OSError:
        log(f"ERROR | File {filename} not found")
        return f"Template {filename} not found"