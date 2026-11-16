"""PIN-area forecast using public MET Norway Locationforecast data."""
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
from threading import Lock
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import os

SOURCE = "https://api.met.no/weatherapi/locationforecast/2.0/documentation"
IST = timezone(timedelta(hours=5, minutes=30))
_cache_lock = Lock()
_cache = {}


def parse_forecast(payload, now):
    properties = payload["properties"]
    updated = datetime.fromisoformat(properties["meta"]["updated_at"])
    if updated < now - timedelta(hours=18) or updated > now + timedelta(minutes=30):
        raise ValueError("Forecast is out of date.")
    complete = [
        (datetime.fromisoformat(row["time"]), row["data"])
        for row in properties["timeseries"]
    ]
    window = [(when, data) for when, data in complete if now - timedelta(minutes=60) <= when <= now + timedelta(hours=72)]
    if not window:
        raise ValueError("No near-term forecast.")
    days = []
    for offset in (0, 1, 2):
        date = (now.astimezone(IST) + timedelta(days=offset)).date()
        rows = [(when, data) for when, data in window if when.astimezone(IST).date() == date]
        if not rows:
            continue
        readings = [data["instant"]["details"] for _, data in rows]
        rain = []
        horizon = rows[-1][0]
        next_time = rows[0][0]
        for when, data in rows:
            if when < next_time:
                continue
            for hours in (6, 1):
                until = when + timedelta(hours=hours)
                forecast = data.get(f"next_{hours}_hours", {}).get("details", {})
                if until.astimezone(IST).date() == date and "precipitation_amount" in forecast:
                    rain.append(float(forecast["precipitation_amount"]))
                    next_time = min(until, horizon + timedelta(hours=6))
                    break
        days.append({
            "date": date.isoformat(), "min_c": min(r["air_temperature"] for r in readings),
            "max_c": max(r["air_temperature"] for r in readings),
            "humidity": sum(r["relative_humidity"] for r in readings) / len(readings),
            "rain_mm": sum(rain) if rain else None, "samples": len(readings),
        })
    instant = window[0][1]["instant"]["details"]
    return {"updated_at": updated.isoformat(), "source": SOURCE, "temperature": instant["air_temperature"],
            "humidity": instant["relative_humidity"], "time": window[0][0].isoformat(), "days": days}


def forecast(lat, lon):
    if lat is None or lon is None:
        return {"reason": "No reliable coordinates were found for this PIN."}
    coords = round(lat, 2), round(lon, 2)
    now = datetime.now(timezone.utc)
    with _cache_lock:
        entry = _cache.get(coords)
        if entry and entry[0] > now:
            return entry[1]
    query = urlencode(dict(zip(("lat", "lon"), coords)))
    user_agent = os.environ.get("SMARTFARM_WEATHER_USER_AGENT", "SmartFarmingIndia-LocalPrototype/1.0")
    request = Request("https://api.met.no/weatherapi/locationforecast/2.0/compact?" + query,
                      headers={"User-Agent": user_agent, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=7) as response:
            result = parse_forecast(json.load(response), now)
            expiry_value = response.headers.get("Expires")
            expires = parsedate_to_datetime(expiry_value) if expiry_value else now + timedelta(minutes=30)
    except (URLError, OSError, KeyError, ValueError, TypeError):
        result = {"reason": "The weather service is unavailable. Crop ranking used the available soil and historical district records."}
        expires = now + timedelta(minutes=3)
    with _cache_lock:
        if len(_cache) >= 256:
            _cache.pop(next(iter(_cache)))
        _cache[coords] = expires, result
    return result
