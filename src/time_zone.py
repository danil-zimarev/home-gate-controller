import time


def _last_sunday(year, month):
    for day in range(31, 24, -1):
        try:
            t = time.mktime((year, month, day, 1, 0, 0, 0, 0, 0))
            if time.localtime(t)[6] == 6:
                return day
        except Exception:
            continue
    return 25

def _is_dst(year, month, day, hour_utc):
    dst_start = _last_sunday(year, 3)
    dst_end = _last_sunday(year, 10)
    if month < 3 or month == 3 and day < dst_start:
        return False
    if month == 3 and day == dst_start:
        return hour_utc >= 1
    if month < 10 or month == 10 and day < dst_end:
        return True
    if month == 10 and day == dst_end:
        return hour_utc < 1
    return False

def tallinn_offset():
    utc = time.localtime(time.time())
    year, month, day, hour = utc[0], utc[1], utc[2], utc[3]
    return 10_800 if _is_dst(year, month, day, hour) else 7_200

def current_time():
    return time.localtime(time.time() + tallinn_offset())
