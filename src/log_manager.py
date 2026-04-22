import uasyncio as asyncio
from config_manager import get_config
import time
import network
import os

LOG_INTERVAL = 3600
LOG_DIR = '../logs'
LOG_PREFIX = 'logs'
LOG_RETENTION_DAYS = 7

def ensure_log_dir():
    try:
        if not LOG_DIR in os.listdir():
            os.mkdir(LOG_DIR)
    except Exception as e:
        print("Error ensuring log directory:", e)

def get_network_state():
    sta_if = network.WLAN(network.STA_IF)
    return f'connected, {sta_if.ifconfig()} ' if sta_if.isconnected() else 'disconnected'

def current_date_str():
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])

def current_time_str():
    t = time.localtime()
    return "{:02d}:{:02d}:{:02d}".format(t[3], t[4], t[5])

def get_log_filename(date_str=None):
    if date_str is None:
        date_str = current_date_str()
    return f"{LOG_DIR}/{LOG_PREFIX}-{date_str}.log"

def log(msg):
    ensure_log_dir()
    filename = get_log_filename()
    timestamp = current_time_str()
    date = current_date_str()
    line = f"{date} - {timestamp} | {msg}\n"
    try:
        with open(filename, 'a') as f:
            f.write(line)
    except Exception as e:
        print("Error writing log:", e)
        
async def log_network_state():
    while True:
        state = get_network_state()
        log(f"Network status: {state}")
        await asyncio.sleep(LOG_INTERVAL)
     
def cleanup_old_logs():
    ensure_log_dir()
    try:
        files = os.listdir(LOG_DIR)
        current_time = time.mktime(time.localtime())
        
        for f in files:
            if f.startswith(LOG_PREFIX) and f.endswith(".log"):
                parts = f.replace('.log', '').replace('logs-', '').split('-')
                try:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                    file_time = time.mktime((y, m, d, 0, 0, 0, 0, 0))
                    age = (current_time - file_time) / 86400
                    if age > LOG_RETENTION_DAYS:
                        os.remove(f"{LOG_DIR}/{f}")
                        log(f"OS | Deleted old log file: {f}")
                except Exception as e:
                        print("Error parsing log date:", f, e)
    except Exception as e:
        print("Error cleaning logs:", e)
        
def get_logs():
    ensure_log_dir()
    logs = []
    
    try:
        files = os.listdir(LOG_DIR)
        for fname in files:
            if fname.endswith(".log"):
                path = f"{LOG_DIR}/{fname}"
                try:
                    with open(path, 'r') as f:
                        content = f.read()
                    logs.append({'name': fname, 'content': content})
                except Exception as e:
                    logs.append({'name': fname, 'error': str(e)})
        return {'status': 'ok', 'logs': logs}
    except Exception as e:
        print(e)
        return {"status": "error", "message": str(e)}

async def periodic_cleanup(interval_hours=24):
    while True:
        try:
            cleanup_old_logs()
        except Exception as e:
            log(f"SYSTEM ERROR | Log cleanup failed: {e}")
        await asyncio.sleep(interval_hours * 3600)