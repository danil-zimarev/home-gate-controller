import os
import time
import network
import uasyncio as asyncio

from src.time_zone import current_time

LOG_INTERVAL = 3_600
LOG_DIR = "logs"
sta = network.WLAN(network.STA_IF)

def _ensure_dir():
    try:
        if LOG_DIR not in os.listdir():
            os.mkdir(LOG_DIR)
    except OSError:
        pass

def format_time(t):
    y, m, d, h, mi, s, *_ = t
    return f"{y:04d}-{m:02d}-{d:02d}", f"{h:02d}:{mi:02d}:{s:02d}"

def network_state():
    return f"connected, {sta.ifconfig()}" if sta.isconnected() else "disconnected"

def log(msg):
    _ensure_dir()
    t = current_time()
    date, clock = format_time(t)
    line = f"{date} - {clock} | {msg}\n"
    file_name = f"{LOG_DIR}/{date}.log"
    try:
        with open(file_name, "a") as f:
            f.write(line)
    except Exception as e:
        print("Log write error:", e)

async def log_network_state():
    while True:
        log(f"Network status: {network_state()}")
        await asyncio.sleep(LOG_INTERVAL)

def cleanup_old_logs():
    _ensure_dir()
    now_epoch = time.mktime(current_time())
    try:
        for f in os.listdir(LOG_DIR):
            if not f.endswith(".log"):
                continue
            try:
                y, m, d = map(int, f.replace(".log", "").split("-")[-3:])
                file_time = time.mktime((y, m, d, 0, 0, 0, 0, 0, 0))
                age_days = (now_epoch - file_time) / 86_400
                if age_days > 7:
                    os.remove(f"{LOG_DIR}/{f}")
                    print(f"OS | deleted {f}")
            except RuntimeError: pass
    except Exception as e:
        print(f"Cleanup error: {e}")

def get_logs():
    _ensure_dir()
    result = []
    try:
        for f in os.listdir(LOG_DIR):
            if not f.endswith(".log"):
                continue
            path = f"{LOG_DIR}/{f}"
            try:
                with open(path, "r") as file:
                    result.append({"name": f, "content": file.read().split("\n")})
            except Exception as e:
                result.append({"name": f, "error": str(e)})
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def periodic_cleanup(hours=24):
    while True:
        cleanup_old_logs()
        await asyncio.sleep(hours * 3600)
