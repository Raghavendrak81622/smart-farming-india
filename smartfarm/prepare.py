"""Rebuild the local lookup database and train the two crop classifiers."""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import zipfile

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from smartfarm.catalog import CROPS, location_key

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "cache"
SOURCES = ROOT / "sources"
CORE = ["ph", "temperature", "humidity"]
NUTRIENTS = ["n", "p", "k"]


def prepare():
    WORK.mkdir(exist_ok=True)
    temp = WORK / "lookup.building"
    temp.unlink(missing_ok=True)
    pins = pd.read_csv(SOURCES / "pins.csv", dtype=str,
                       usecols=["Pincode", "OfficeName", "StateName", "District", "Latitude", "Longitude"])
    pins = pins.dropna(subset=["Pincode", "StateName", "District"]).copy()
    test_office = pins.OfficeName.str.strip().str.casefold().eq("test office").fillna(False)
    pins = pins.loc[pins.Pincode.str.fullmatch("[1-9][0-9]{5}") & ~test_office]
    for key, bounds in (("Latitude", (6, 39)), ("Longitude", (66, 101))):
        values = pd.to_numeric(pins[key], errors="coerce")
        pins[key] = values.where(values.between(*bounds))
    pins[["StateName", "District"]] = pins[["StateName", "District"]].apply(lambda column: column.str.strip().str.title())
    points = pins.groupby(["Pincode", "StateName", "District"], as_index=False).agg(
        lat=("Latitude", "median"), lon=("Longitude", "median"), offices=("Pincode", "size")
    )
    points.columns = ["pin", "state", "district", "lat", "lon", "offices"]

    apy = pd.read_csv(SOURCES / "production.csv")
    ids = {value[1]: key for key, value in CROPS.items()}
    apy = apy.loc[apy.Crop.isin(ids) & apy.Season.isin(["Kharif", "Rabi", "Summer"]) &
                  apy.Area.gt(0) & apy.Production.gt(0)].drop_duplicates().copy()
    apy["crop"] = apy.Crop.map(ids)
    apy["state"] = apy.State_Name.map(location_key)
    apy["district"] = apy.District_Name.map(location_key)
    apy["season"] = apy.Season.str.lower()
    apy["year"] = apy.Crop_Year
    apy = apy.loc[(apy.Production / apy.Area).between(.01, 20)]
    annual = apy.groupby(["state", "district", "crop", "season", "year"], as_index=False)[["Area", "Production"]].sum()

    allowed = {name.casefold(): code for code, (_, _, names, _, _) in CROPS.items() for name in names}
    def prices(frame, date_format):
        frame.columns = frame.columns.str.replace("_x0020_", "_", regex=False)
        frame["crop"] = frame.Commodity.str.strip().str.casefold().map(allowed)
        frame = frame.dropna(subset=["crop", "State", "District", "Market", "Variety", "Grade"]).copy()
        frame["date"] = pd.to_datetime(frame.Arrival_Date, errors="coerce", format=date_format).dt.strftime("%Y-%m-%d")
        frame["price"] = pd.to_numeric(frame.Modal_Price, errors="coerce")
        frame["state"] = frame.State.map(location_key)
        frame["district"] = frame.District.map(location_key)
        return frame.loc[frame.price.between(0.01, 1e6) & frame.date.notna(),
                         ["crop", "state", "district", "Market", "Commodity", "Variety", "Grade", "date", "price"]]

    bulletin = ROOT / "9ef84268-d588-465a-a308-a864a43d0070.csv"
    batches = [prices(pd.read_csv(bulletin), "%d/%m/%Y")]
    with zipfile.ZipFile(ROOT / "archive (1).zip") as archive, archive.open("csv/2026.csv") as recent:
        batches.extend(prices(chunk, "%Y-%m-%d") for chunk in pd.read_csv(recent, chunksize=100_000))
    quotes = pd.concat(batches, ignore_index=True).drop_duplicates()

    with closing(sqlite3.connect(temp)) as db, db:
        points.to_sql("pins", db, index=False)
        annual.to_sql("yields", db, index=False)
        quotes.to_sql("quotes", db, index=False)
        db.execute("CREATE INDEX pins_lookup ON pins(pin)")
        db.execute("CREATE INDEX yield_lookup ON yields(state,season,crop,district,year)")
        db.execute("CREATE INDEX quotes_lookup ON quotes(crop,state,district,date)")
    temp.replace(WORK / "evidence.sqlite")

    data = pd.read_csv(ROOT / "Crop_recommendation.csv")
    data.columns = data.columns.str.lower()
    data = data.loc[data.label.isin(CROPS)].copy()
    train, test = train_test_split(data, test_size=.2, random_state=112, stratify=data.label)
    models, scores = {}, {}
    for mode, columns in (("weather", CORE), ("native", CORE + NUTRIENTS), ("soil", ["ph"]),
                          ("soil_native", ["ph"] + NUTRIENTS)):
        model = RandomForestClassifier(n_estimators=140, min_samples_leaf=4, random_state=112, n_jobs=2)
        model.fit(train[columns], train.label)
        scores[mode] = accuracy_score(test.label, model.predict(test[columns]))
        models[mode] = {"model": model, "fields": columns}
    joblib.dump(models, WORK / "crops.joblib", compress=3)
    holdout_errors = []
    for _, series in annual.groupby(["state", "district", "crop", "season"]):
        values = series.sort_values("year")
        recent = values.iloc[-6:]
        rates = (recent.Production / recent.Area).to_numpy()
        if len(rates) >= 4 and recent.year.iloc[-1] >= 2018:
            holdout_errors.append(abs(float(np.median(rates[:-1])) - rates[-1]))
    audit = {
        "postal_candidates": len(points), "district_crop_season_years": len(annual), "price_rows": len(quotes),
        "crop_classifier_source_holdout_rows": len(test), "source_holdout_accuracy": scores,
        "yield_latest_year_holdout_groups": len(holdout_errors),
        "yield_latest_year_holdout_mae_t_per_ha": float(np.mean(holdout_errors)) if holdout_errors else None,
    }
    (WORK / "validation.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
