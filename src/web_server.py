import ujson
import uasyncio as asyncio
import machine

from microdot import Microdot, Response
from config_manager import get_config, update_config
from pin_manager import init_pins, toggle_pin
from log_manager import log, get_logs

app = Microdot()
Response.default_content_type = "text/html"

# Pins 16+ are active-low relays: True = relay off (safe default)
PIN_STATES = {str(p): False if p < 16 else True for p in range(29)}
PIN_STATES["LED"] = False


def json_response(data, status=200):
    return Response(ujson.dumps(data), status_code=status, headers={"Content-Type": "application/json"})

def render_template(path, context=None):
    context = context or {}
    try:
        with open(path) as f:
            html = f.read()
        for k, v in context.items():
            html = html.replace(f"{{{{{k}}}}}", str(v))
        return html
    except OSError:
        return f"Template {path} not found"

def sorted_pins(pins):
    numeric = sorted((p for p in pins if p.isdigit()), key=int)
    other = [p for p in pins if not p.isdigit()]
    return numeric + other

@app.get("/")
def index(request):
    conf = get_config()
    wifi = conf.get("wifi", {})
    pins = conf.get("pins", {})
    pin_checkboxes = []
    pin_toggles = []

    for p in sorted_pins(pins):
        pin = str(p)
        data = pins[pin]
        enabled = data.get("enabled", False)
        pin_checkboxes.append(
            f'<label><input type="checkbox" name="{pin}" {"checked" if enabled else ""}/> GPIO {pin}</label>'
        )

        if enabled:
            state = PIN_STATES.get(pin, False)
            # Render toggle with class names so client can switch classes (on/off) for coloring
            cls = "on" if state else "off"
            text = "ON" if state else "OFF"
            pin_toggles.append(
                f'<a href="/toggle/{pin}" class="pin-toggle-link" data-pin="{pin}">'
                + f'GPIO {pin} <span class="toggle-state {cls}">{text}</span>'
                + '</a>'
            )

    html = render_template("www/index.html", {
        "ssid": wifi.get("ssid", ""),
        "password": wifi.get("password", ""),
        "ip": wifi.get("ip", ""),
        "mask": wifi.get("mask", ""),
        "dns": wifi.get("dns", ""),
        "gw": wifi.get("gw", ""),
        "pin_checkboxes": "".join(pin_checkboxes),
        "pin_toggles": "".join(pin_toggles)
    })
    return Response(html)


def _build_pin_toggles_html():
    conf = get_config()
    pins = conf.get("pins", {})
    pin_toggles = []

    for p in sorted_pins(pins):
        pin = str(p)
        data = pins[pin]
        enabled = data.get("enabled", False)

        if enabled:
            state = PIN_STATES.get(pin, False)
            cls = "on" if state else "off"
            text = "ON" if state else "OFF"
            pin_toggles.append(
                f'<a href="/toggle/{pin}" class="pin-toggle-link" data-pin="{pin}">'
                + f'GPIO {pin} <span class="toggle-state {cls}">{text}</span>'
                + '</a>'
            )

    return "".join(pin_toggles)


@app.get('/pin_toggles')
def pin_toggles_fragment(request):
    """Return the HTML fragment for the pin toggle list."""
    try:
        html = _build_pin_toggles_html()
        return Response(html)
    except Exception as e:
        log(f"ERROR | pin_toggles_fragment: {e}")
        return Response("", status_code=500)


@app.post("/toggle/<pin>")
def toggle(request, pin):
    pins = get_config().get("pins", {})

    if pin not in pins:
        return json_response({"status": "error", "message": "Invalid Pin"}, 400)

    state = toggle_pin(pin)
    if state is None:
        return json_response({"status": "error", "message": "Pin not initialized"}, 400)
    PIN_STATES[pin] = state
    return json_response({"status": "ok", "pin": pin, "state": state})


@app.post("/save_network")
def save_network(request):
    try:
        data = request.json or {}
        required = ("ssid", "password")
        optional = ("ip", "mask", "dns", "gw")
        conf = get_config()
        conf["wifi"] = {k: data[k] for k in required}
        conf["wifi"].update({k: data.get(k, "") for k in optional})
        update_config(conf)
        return json_response({"status": "ok"})
    except Exception as e:
        log(f"ERROR | save_network: {e}")
        return json_response({"status": "error", "message": str(e)}, 500)

@app.post("/save_pins")
def save_pins(request):
    try:
        data = request.json or {}
        enabled = data.get("enabled_pins", {})
        if not isinstance(enabled, dict):
            return json_response({"status": "error", "message": "Invalid data"}, 400)
        conf = get_config()
        pins = conf.get("pins", {})

        for pin, value in enabled.items():
            if pin in pins:
                pins[pin]["enabled"] = bool(value)

        update_config(conf)
        init_pins()
        return json_response({"status": "ok"})
    except Exception as e:
        log(f"ERROR | save_pins: {e}")
        return json_response({"status": "error", "message": str(e)}, 500)


@app.get("/logs")
def logs_endpoint(request):
    return json_response(get_logs())

@app.get("/reload")
def reload_pico(request):
    log("SYSTEM | Reload requested")
    asyncio.create_task(_delayed_reboot())
    return json_response({"status": "ok", "message": "Rebooting..."})

async def _delayed_reboot():
    await asyncio.sleep(1)
    machine.reset()
