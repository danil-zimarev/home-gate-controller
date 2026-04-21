import ujson

CONFIG_FILE = "config.json"
CONFIG = None

def _load_from_disk():
    global CONFIG
    with open(CONFIG_FILE, 'r') as f:
        CONFIG = ujson.load(f)
    return CONFIG

def _save_to_disk():
    global CONFIG
    with open(CONFIG_FILE, 'w') as f:
        ujson.dump(CONFIG, f)
        
def init_config():
    global CONFIG
    if CONFIG is None:
        _load_from_disk()
        
def get_config():
    global CONFIG
    if CONFIG is None:
        _load_from_disk()
    return CONFIG

def update_config(new_conf):
    global CONFIG
    CONFIG = new_conf
    _save_to_disk()
    
def save_config():
    _save_to_disk()
