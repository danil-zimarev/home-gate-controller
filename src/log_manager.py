import os
import time
import network
import uasyncio as asyncio

LOG_INTERVAL = 3600
LOG_DIR = 'logs'
LOG_PREFIX = 'logs'
LOG_RETENTION_DAYS = 7
sta = network.WLAN(network.STA_IF)
TIMEZONE_OFFSET = 3 * 3600


# ------------------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------------------
def _ensure_dir():
    try:
        if LOG_DIR not in os.listdir():
            os.mkdir(LOG_DIR)
    except OSError as e:
        pass


def now():
    return time.localtime(time.time() + TIMEZONE_OFFSET)

def date_str():
    y, m, d, *_ = now()
    return f'{y:04d}-{m:02d}-{d:02d}'

def time_str():
    _, _, _, h, mi, s, *_ = now()
    return f'{h:02d}:{mi:02d}:{s:02d}'

def log_file():
    return f'{LOG_DIR}/{LOG_PREFIX}-{date_str()}.log'

def network_state():
    return f'connected, {sta.ifconfig()}' if sta.isconnected() else 'disconnected'

def log(msg):
    _ensure_dir()
    line = f'{date_str()} - {time_str()} | {msg}\n'
    print(line[:-2])
    try:
        with open(log_file(), 'a') as f:
            f.write(line)
    except Exception as e:
        print('LOG WRITE ERROR:', e)

async def log_network_state():
    while True:
        log(f'Network status: {network_state()}')
        await asyncio.sleep(LOG_INTERVAL)

def cleanup_old_logs():
    _ensure_dir()
    now = time.mktime(time.localtime())
    try:
        for f in os.listdir(LOG_DIR):
            if not f.endswith('.log'):
                continue
            try:
                y, m, d = map(int, f.replace('.log', '').split('-')[-3:])
                file_time = time.mktime((y, m, d, 0, 0, 0, 0, 0))
                age_days = (now - file_time) / (24 * 3600)
                if age_days > LOG_RETENTION_DAYS:
                    os.remove(f'{LOG_DIR}/{f}')
                    print(f'OS | deleted {f}')
            except: pass
    except Exception as e:
        print(f'Cleanup error: {e}')


def get_logs():
    _ensure_dir()
    result = []
    try:
        for f in os.listdir(LOG_DIR):
            if not f.endswith('.log'):
                continue
            path = f'{LOG_DIR}/{f}'
            try:
                with open(path, 'r') as file:
                    result.append({'name': f, 'content': file.read().split('\n')})
            except Exception as e:
                result.append({'name': f, 'error': str(e)})
        return result
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


async def periodic_cleanup(hours=24):
    while True:
        try:
            cleanup_old_logs()
        except Exception as e:
            pass
        await asyncio.sleep(hours * 3600)
