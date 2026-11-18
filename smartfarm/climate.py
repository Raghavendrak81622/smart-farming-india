"""Prepare seasonal rainfall normals from local IMD grid files."""
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np

MONTHS = {"Kharif": (6, 7, 8, 9), "Rabi": (10, 11, 12, 1, 2), "Zaid": (3, 4, 5)}


def prepare_climate(root, work):
    from scipy.io import netcdf_file

    days, surfaces = [], []
    for path in sorted(root.glob("RFone_imd_rf_1x1_*.nc")):
        if not path.stat().st_size:
            continue
        with netcdf_file(path, mmap=False, maskandscale=True) as dataset:
            lat = np.array(dataset.variables["LATITUDE"][:], dtype=float)
            lon = np.array(dataset.variables["LONGITUDE"][:], dtype=float)
            rain = np.ma.asarray(dataset.variables["RAINFALL"][:], dtype=float)
            surfaces.append(rain.filled(np.nan))
            days.extend(date(1900, 12, 31) + timedelta(days=int(value)) for value in dataset.variables["TIME"][:])
    if not days:
        return
    rain = np.concatenate(surfaces)
    rain[(rain < 0) | ~np.isfinite(rain)] = np.nan
    years = sorted({day.year for day in days})
    results = {}
    for season, months in MONTHS.items():
        totals = []
        for year in years:
            if season == "Rabi" and year == years[-1]:
                continue
            selected = [i for i, day in enumerate(days) if day.month in months and
                        (day.year - (season == "Rabi" and day.month <= 2)) == year]
            first = date(year, months[0], 1)
            end = date(year + (season == "Rabi"), months[-1] + 1, 1)
            expected = (end - first).days
            if len(selected) != expected or len({days[i] for i in selected}) != expected:
                continue
            values = rain[selected]
            totals.append(np.where(np.isfinite(values).all(axis=0), np.sum(values, axis=0), np.nan))
        if not totals:
            results[season] = np.full((len(lat), len(lon)), np.nan)
            continue
        stacked = np.stack(totals)
        counts = np.sum(np.isfinite(stacked), axis=0)
        results[season] = np.divide(np.nansum(stacked, axis=0), counts, out=np.full(counts.shape, np.nan), where=counts >= 3)
    np.savez_compressed(work / "seasonal_rainfall.npz", lat=lat, lon=lon, **results)


@lru_cache(maxsize=2)
def load(path, modified):
    with np.load(path, allow_pickle=False) as grids:
        return dict(grids)


def seasonal_rain(work, latitude, longitude, season):
    path = work / "seasonal_rainfall.npz"
    if latitude is None or longitude is None or not path.is_file():
        return None
    grids = load(path, path.stat().st_mtime_ns)
    iy = int(np.argmin(abs(grids["lat"] - latitude)))
    ix = int(np.argmin(abs(grids["lon"] - longitude)))
    if abs(grids["lat"][iy] - latitude) > .55 or abs(grids["lon"][ix] - longitude) > .55:
        return None
    value = grids[season][iy, ix]
    return float(value) if np.isfinite(value) else None
