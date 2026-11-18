"""Single workflow for Indian farm recommendations, field alerts and returns."""
from contextlib import closing
from datetime import datetime, timezone, date
from pathlib import Path
import sqlite3
import re
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from statistics import mean, median

from smartfarm.catalog import ACRE_TO_HA, CROPS, COST_SOURCE, YIELD_SOURCE, location_key
from smartfarm.guidance import guidance
from smartfarm.weather import IST
from smartfarm.agronomy import SEASONS, assess, nutrient_summary, public_guide
from smartfarm.climate import seasonal_rain
from smartfarm.soil_report import import_report
from smartfarm.plans import register_draft, router as plans_router

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "cache"
app = FastAPI(title="Fieldwise", docs_url=None, redoc_url=None)
app.include_router(plans_router)
app.add_api_route("/api/soil-report", import_report, methods=["POST"])


class Farm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)
    pin: str = Field(pattern=r"^[1-9][0-9]{5}$")
    location_index: int = Field(default=0, ge=0, le=100)
    acres: float = Field(gt=0, le=10000)
    ph: float = Field(ge=0, le=14)
    n: float = Field(ge=0, le=100000)
    p: float = Field(ge=0, le=100000)
    k: float = Field(ge=0, le=100000)
    season: Literal["Kharif", "Rabi", "Zaid"]
    irrigation: Literal["Rainfed", "Partially irrigated", "Irrigated"]
    soil_type: Literal["Unknown", "Sandy", "Loamy", "Clay", "Red", "Black", "Alluvial", "Laterite"] = "Unknown"
    nutrient_unit: Literal["kg_ha", "other"] = "kg_ha"
    previous_crop: str = Field(default="", max_length=100)


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
    if not re.fullmatch(r"[1-9][0-9]{5}", pin):
        raise HTTPException(422, "Enter a six-digit Indian PIN beginning with 1–9.")
    options = pin_options(pin)
    if not options:
        raise HTTPException(404, "This PIN is missing from the local India Post directory.")
    return {"locations": [{"state": row["state"], "district": row["district"]} for row in options]}


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
    scenarios = {}
    for name, rate in zip(("conservative", "average", "optimistic"), (rates[0], mean(rates), rates[-1])):
        scenarios[name] = {"quintals_per_acre": rate * ACRE_TO_HA * 10, "quintals": rate * hectares * 10}
    return {"scenarios": scenarios, "scope": scope, "years": sorted(row["year"] for row in rows),
            "source": YIELD_SOURCE, "basis": "Reported rice; paddy or milled basis unknown" if crop == "rice" else "Reported whole grain"}


def market_quote(db, state, district, crop, as_of):
    columns = {row[1] for row in db.execute("PRAGMA table_info(quotes)")}
    units = "unit,source" if "unit" in columns else "NULL AS unit,NULL AS source"
    sql = """SELECT Market AS market, Commodity AS commodity, Variety AS variety, Grade AS grade,
             date, price, {units} FROM quotes WHERE crop=? AND state=? AND date<=? {district_filter}
             ORDER BY date DESC,Market,Variety,Grade LIMIT 250"""
    base = (crop, state, as_of)
    rows = db.execute(sql.format(district_filter="AND district=?", units=units), (*base, district)).fetchall()
    scope = "District"
    if not rows:
        rows = db.execute(sql.format(district_filter="", units=units), base).fetchall()
        scope = "State"
    if not rows:
        return None
    verified = [row for row in rows if row["unit"] == "INR/quintal" and row["source"]]
    candidates = verified or rows
    matches = [row for row in candidates if row["date"] == candidates[0]["date"]]
    midpoint = median(row["price"] for row in matches)
    selected = min(matches, key=lambda row: abs(row["price"] - midpoint))
    stale = (date.fromisoformat(as_of) - date.fromisoformat(selected["date"])).days > 30
    return {**dict(selected), "scope": scope, "verified": bool(verified), "stale": stale}


def choose_location(pin, index):
    locations = pin_options(pin)
    if not locations:
        raise HTTPException(404, "This PIN is missing from the local India Post directory.")
    if not 0 <= index < len(locations):
        raise HTTPException(422, "Choose one of the districts listed for this PIN.")
    return locations[index]


def catalogue():
    return [{"crop": key, "name": record[0], "guide": public_guide(key), **guidance(key)} for key, record in CROPS.items()]


app.get("/api/crops")(catalogue)


@app.get("/api/market/{pin}")
def markets(pin: str, location_index: int = 0):
    place = choose_location(pin, location_index)
    as_of = datetime.now(timezone.utc).astimezone(IST).date().isoformat()
    with closing(connect()) as db:
        return [{"crop": key, "name": record[0], "market": market_quote(
            db, location_key(place["state"]), location_key(place["district"]), key, as_of
        )} for key, record in CROPS.items()]


@app.post("/api/recommend")
def recommend(farm: Farm):
    place = choose_location(farm.pin, farm.location_index)
    now = datetime.now(timezone.utc).astimezone(IST)
    season = SEASONS[farm.season]
    state, district = location_key(place["state"]), location_key(place["district"])
    hectares = farm.acres * ACRE_TO_HA
    climate_mm = seasonal_rain(STORE, place["lat"], place["lon"], farm.season)
    low, nutrients = nutrient_summary(farm)
    crops = []
    with closing(connect()) as db:
        for crop, (name, _, _, cost_season, cost_rate) in CROPS.items():
            production = historical_yield(db, state, district, crop, season, hectares)
            if not production:
                continue
            price = market_quote(db, state, district, crop, now.date().isoformat())
            # The source calls this crop rice. Its paddy vs. milled basis is not confirmed.
            compatible = crop != "rice"
            cost = production["scenarios"]["average"]["quintals"] * cost_rate if compatible and season == cost_season.casefold() else None
            profile = public_guide(crop)
            suitability = assess(crop, farm, production, climate_mm, low, state)
            crops.append({
                "crop": crop, "name": name, "suitability": suitability, "guide": profile, "yield": production,
                "market": price, "estimated_cost": cost, "cost_rate": cost_rate if cost is not None else None,
                "cost_source": COST_SOURCE if cost is not None else None,
                "price_calculation_available": compatible,
                **guidance(crop),
            })
    order = {"High": 0, "Moderate": 1, "Low": 2}
    crops.sort(key=lambda crop: (order[crop["suitability"]["category"]],
                                crop["yield"]["scope"] != "District", len(crop["suitability"]["cautions"]),
                                -max(crop["yield"]["years"]), crop["name"]))
    return register_draft({
        "location": {key: place[key] for key in ("state", "district")},
        "farm": farm.model_dump(), "created_at": now.isoformat(timespec="seconds"),
        "season": farm.season, "acres": farm.acres, "hectares": hectares,
        "soil_note": nutrients, "crops": crops[:5], "budgets": {},
    })


@app.get("/")
def home():
    return FileResponse(ROOT / "web/index.html")


app.mount("/assets", StaticFiles(directory=ROOT / "web/assets"), name="assets")
