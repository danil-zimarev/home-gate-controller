import ujson

CONFIG_FILE = "config.json"
CONFIG = None

def _load():
    global CONFIG
    with open(CONFIG_FILE, 'r') as f:
        CONFIG = ujson.load(f)
    return CONFIG

def _save():
    if CONFIG is None:
        return
    with open(CONFIG_FILE, 'w') as f:
        ujson.dump(CONFIG, f)

def _ensure_loaded():
    if CONFIG is None:
        _load()

def get_config():
    _ensure_loaded()
    return CONFIG

def update_config(conf):
    global CONFIG
    CONFIG = conf
    _save()

