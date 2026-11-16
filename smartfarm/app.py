"""Single workflow for Indian farm recommendations, field alerts and returns."""
from contextlib import closing
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
import joblib
import pandas as pd

from smartfarm.catalog import ACRE_TO_HA, CROPS, COST_SOURCE, YIELD_SOURCE, location_key
from smartfarm.guidance import guidance
from smartfarm.weather import forecast, IST

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "cache"
app = FastAPI(title="Smart Farming India", docs_url=None, redoc_url=None)


class Farm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)
    pin: str = Field(pattern=r"^[1-9][0-9]{5}$")
    location_index: int = Field(default=0, ge=0, le=100)
    acres: float = Field(gt=0, le=10000)
    ph: float = Field(ge=0, le=14)
    n: float | None = Field(default=None, ge=0, le=100000)
    p: float | None = Field(default=None, ge=0, le=100000)
    k: float | None = Field(default=None, ge=0, le=100000)
    source_scale: bool = False


def connect():
    source = STORE / "evidence.sqlite"
    if not source.exists():
        raise HTTPException(503, "Run Start-Farming.ps1 prepare to build the lookup data.")
    db = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    return db


def pin_options(pin):
    with closing(connect()) as db:
        return [dict(row) for row in db.execute(
            "SELECT state,district,lat,lon FROM pins WHERE pin=? ORDER BY offices DESC,state,district", (pin,)
        )]


@app.get("/api/pins/{pin}")
def pin_location(pin: str):
    import re
    if not re.fullmatch(r"[1-9][0-9]{5}", pin):
        raise HTTPException(422, "Enter a six-digit Indian PIN beginning with 1–9.")
    options = pin_options(pin)
    if not options:
        raise HTTPException(404, "This PIN is missing from the local India Post directory.")
    return {"locations": [{"state": row["state"], "district": row["district"]} for row in options]}


def current_season(month):
    if 6 <= month <= 9:
        return "kharif"
    return "rabi" if month >= 10 or month <= 2 else "summer"


def historical_yield(db, state, district, crop, season, hectares):
    args = (state, season, crop)
    recent = """SELECT year,sum(Production)/sum(Area) AS tonnes_ha FROM yields
                WHERE state=? AND season=? AND crop=? {district_filter}
                GROUP BY year ORDER BY year DESC LIMIT 5"""
    rows = db.execute(recent.format(district_filter="AND district=?"), (*args, district)).fetchall()
    scope = "District"
    if len(rows) < 3 or rows[0]["year"] < 2018:
        rows = db.execute(recent.format(district_filter=""), args).fetchall()
        scope = "State"
    if len(rows) < 3 or rows[0]["year"] < 2018:
        return None
    rates = sorted(row["tonnes_ha"] for row in rows)
    rate = float(pd.Series(rates).median())
    return {"tonnes_per_ha": rate, "tonnes": rate * hectares, "range_tonnes": [rates[0]*hectares, rates[-1]*hectares],
            "scope": scope, "years": sorted(row["year"] for row in rows), "source": YIELD_SOURCE}


def market_quote(db, state, district, crop, as_of):
    sql = """SELECT Market AS market, Commodity AS commodity, Variety AS variety, Grade AS grade,
             date, price FROM quotes WHERE crop=? AND state=? AND date<=? {district_filter}
             ORDER BY date DESC,Market,Variety,Grade LIMIT 250"""
    base = (crop, state, as_of)
    rows = db.execute(sql.format(district_filter="AND district=?"), (*base, district)).fetchall()
    scope = "District"
    if not rows:
        rows = db.execute(sql.format(district_filter=""), base).fetchall()
        scope = "State"
    if not rows:
        return None
    matches = [row for row in rows if row["date"] == rows[0]["date"]]
    midpoint = float(pd.Series([row["price"] for row in matches]).median())
    selected = min(matches, key=lambda row: abs(row["price"] - midpoint))
    return {**dict(selected), "scope": scope}


@lru_cache(maxsize=1)
def classifiers():
    artifact = STORE / "crops.joblib"
    if not artifact.exists():
        raise HTTPException(503, "Run Start-Farming.ps1 prepare to train the crop model.")
    return joblib.load(artifact)


def model_scores(farm, weather):
    readings = {field: getattr(farm, field) for field in ("ph", "n", "p", "k")}
    native = (farm.source_scale and all(readings[key] is not None for key in ("n", "p", "k"))
              and 0 <= readings["n"] <= 140 and 5 <= readings["p"] <= 145 and 5 <= readings["k"] <= 205)
    uses_weather = "temperature" in weather
    if uses_weather:
        readings.update(temperature=weather["temperature"], humidity=weather["humidity"])
    mode = ("native" if native else "weather") if uses_weather else ("soil_native" if native else "soil")
    config = classifiers()[mode]
    frame = pd.DataFrame([readings], columns=config["fields"])
    model = config["model"]
    if not 3.5 <= farm.ph <= 9.95:
        return {}, config["fields"], "Soil pH is outside the useful reference range. Check the reading before using scores."
    note = ("Model scores use pH" + (", confirmed reference-scale NPK" if native else "") +
            (" and the near-term forecast’s temperature and humidity." if uses_weather else "."))
    if any(readings[key] is not None for key in ("n", "p", "k")) and not native:
        note += " Entered NPK is shown in your soil report. The reference file’s nutrient units cannot be verified."
    return dict(zip(model.classes_, map(float, model.predict_proba(frame)[0]))), config["fields"], note


@app.post("/api/recommend")
def recommend(farm: Farm):
    locations = pin_options(farm.pin)
    if not locations:
        raise HTTPException(404, "This PIN is missing from the local India Post directory.")
    if farm.location_index >= len(locations):
        raise HTTPException(422, "Choose one of the districts listed for this PIN.")
    place = locations[farm.location_index]
    weather = forecast(place["lat"], place["lon"])
    now = datetime.now(timezone.utc).astimezone(IST)
    season = current_season(now.month)
    state, district = location_key(place["state"]), location_key(place["district"])
    hectares = farm.acres * ACRE_TO_HA
    scores, fields, note = model_scores(farm, weather)
    crops = []
    with closing(connect()) as db:
        for crop, (name, _, _, cost_season, cost_rate) in CROPS.items():
            production = historical_yield(db, state, district, crop, season, hectares)
            if not production:
                continue
            price = market_quote(db, state, district, crop, now.date().isoformat())
            # The source calls this crop rice. Its paddy vs. milled basis is not confirmed.
            compatible = crop != "rice"
            cost = production["tonnes"] * 10 * cost_rate if compatible and season == cost_season.casefold() else None
            crops.append({
                "crop": crop, "name": name, "score": scores.get(crop), "yield": production,
                "market": price, "estimated_cost": cost, "cost_rate": cost_rate if cost is not None else None,
                "cost_source": COST_SOURCE if cost is not None else None,
                "price_calculation_available": compatible,
                **guidance(crop),
            })
    crops.sort(key=lambda crop: (crop["yield"]["scope"] != "District", -(crop["score"] or 0), crop["name"]))
    return {
        "location": {key: place[key] for key in ("state", "district")},
        "season": season.title(), "acres": farm.acres, "hectares": hectares,
        "weather": weather, "soil": {key: getattr(farm, key) for key in ("n", "p", "k", "ph")},
        "model_fields": fields if scores else [], "model_note": note, "crops": crops[:3],
    }


@app.get("/")
def home():
    return FileResponse(ROOT / "web/index.html")


app.mount("/assets", StaticFiles(directory=ROOT / "web/assets"), name="assets")
