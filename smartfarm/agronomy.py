"""Sourced cultivation references and conservative field screening rules."""
from smartfarm.catalog import COST_SOURCE, CROPS

SOIL_REFERENCE = "https://soilhealth.dac.gov.in/files/Manual/14072023Manual_Class_9_10.pdf"
WATER_REFERENCE = "https://www.fao.org/4/s2022e/s2022e02.htm"
TNAU = "https://agritech.tnau.ac.in/"
GUIDES = {
    "rice": {
        "duration": "105–135 days in the cited variety examples",
        "water": "High. Reliable water control for transplanted lowland systems.",
        "water_floor": 450,
        "soil": "A level field with water control is important for the transplanted lowland method.",
        "land": "Level the field, prepare the nursery near the water source, and puddle according to the local transplanting system.",
        "seed": "About 12 kg/acre for the cited long-duration nursery seed rate of 30 kg/ha. Short-duration types use a different rate.",
        "sow": "Transplant seedlings from a nursery. The guide varies hill spacing with variety and soil fertility.",
        "irrigation": "Coordinate water depth with establishment and crop stage. Confirm the field drainage and water schedule locally.",
        "harvest": "Cut once the selected variety has matured and grain is firm. Check moisture before storage.",
        "source": TNAU + "expert_system/paddy/riceecosystem.html",
    },
    "maize": {
        "duration": "About 100–140 days, depending on variety and growing system",
        "water": "Medium to high. Protect crop moisture around tasselling and silking.",
        "water_floor": 500,
        "soil": "Use a well-drained seedbed. Avoid standing water.",
        "land": "Prepare a drained seedbed. Choose ridges, furrows or beds that suit the field and irrigation method.",
        "seed": "About 8.1 kg/acre for the cited irrigated grain hybrids at 20 kg/ha.",
        "sow": "The cited irrigated example uses 60 cm rows, with 25 cm between plants.",
        "irrigation": "Check soil moisture at establishment, tasselling and silking. Adjust intervals to the field and variety.",
        "harvest": "For grain maize, wait until kernels harden and the husks dry. Confirm harvest moisture for storage.",
        "source": TNAU + "CropProduction/Millets/millets_maize.html",
    },
    "chickpea": {
        "duration": "About 85 days for the cited CO varieties",
        "water": "Avoid standing water. If irrigating, check moisture around flowering and pod formation.",
        "soil": "Well-drained soil is important. The reference chickpea pH range is 6.0–7.5, with caution above it.",
        "ph": (6, 7.5),
        "land": "Prepare a fine, well-drained seedbed. Rotate away from chickpea where wilt is recurring.",
        "seed": "About 30 kg/acre for CO 4 at 75 kg/ha. Confirm the rate for your variety and seed size.",
        "sow": "Line sow. The production guide lists spacing by variety and establishment method.",
        "irrigation": "Where irrigation is available, schedule from field moisture and avoid waterlogging.",
        "harvest": "Harvest when most pods have matured and dried and dry the grain for storage.",
        "source": TNAU + "agriculture/pulses_bengalgram.html",
        "soil_source": "https://krishikosh.egranth.ac.in/server/api/core/bitstreams/4d64814e-1265-4335-a6e5-72f6be274ba5/content",
    },
    "pigeonpeas": {
        "duration": "Variety dependent. Short-, medium- and long-duration types are available.",
        "water": "Dryland varieties are available. Check moisture at flowering and pod development.",
        "soil": "Use a drained field. Tamil Nadu dryland examples include red and lateritic soils.",
        "land": "Prepare a drained seedbed and choose a system suited to sole cropping or intercropping.",
        "seed": "Use the variety- and system-specific seed rate in the local package. Sole crops and intercrops differ.",
        "sow": "Dryland examples use 45 cm row spacing for short or medium types and 90 cm for some long types.",
        "irrigation": "Check soil moisture at bud formation, flowering and pod development before supplemental irrigation.",
        "harvest": "Start when most pods have matured. Confirm the variety-specific harvest stage locally.",
        "source": TNAU + "agriculture/pulses_redgram.html",
    },
    "mungbean": {
        "duration": "70–75 days for the cited rice-fallow variety",
        "water": "Avoid pooling. Check soil moisture at flowering and pod formation.",
        "soil": "Well-drained soil is preferred. FAO lists an optimal pH of 5.5–6.2.",
        "ph": (5.5, 6.2), "ph_limit": (4.3, 8.3),
        "land": "Prepare a well-drained seedbed or follow the separate rice-fallow package where applicable.",
        "seed": "About 8.1 kg/acre in the cited sole-crop example at 20 kg/ha. Rice-fallow rates differ.",
        "sow": "Follow the local sole-crop spacing or the separate relay seeding method for a rice fallow.",
        "irrigation": "Check establishment moisture and protect flowering and pod formation without leaving standing water.",
        "harvest": "Check that most pods have turned dark and the seeds are hard before picking.",
        "source": TNAU + "agriculture/pulses_greengram.html",
        "soil_source": "https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=2150",
    },
    "blackgram": {
        "duration": "60–75 days among the cited varieties",
        "water": "Drained beds. Irrigate according to field moisture and avoid standing water.",
        "soil": "The cited irrigated package prefers well-drained soil.",
        "land": "Prepare fine tilth and level the field. Make beds and channels where irrigation is used.",
        "seed": "About 8.1 kg/acre in the cited irrigated example at 20 kg/ha.",
        "sow": "Use local row spacing and seed rate for the selected irrigated, dryland or relay system.",
        "irrigation": "The irrigated reference checks moisture every 7–10 days. Confirm the interval for your field.",
        "harvest": "Harvest around physiological maturity, when most pods are mature, to limit shattering losses.",
        "source": TNAU + "agriculture/CropProduction/Pulses/BlackgramIrrigated.html",
    },
}

SEASONS = {"Kharif": "kharif", "Rabi": "rabi", "Zaid": "summer"}
# Government Soil Sampling & Testing Manual classes for available elemental nutrients.
NUTRIENT_LIMITS = {"n": 280, "p": 10, "k": 120}
NAMES = {"n": "nitrogen", "p": "phosphorus", "k": "potassium"}
# State-level ICAR calendars in Agricultural Statistics at a Glance, Appendix V.
WINDOWS = {
    ("maharashtra", "maize", "Kharif"): ("Early July to early August", "Early October to early November", 462),
    ("maharashtra", "maize", "Rabi"): ("Mid-October to mid-December", "Early March to early May", 462),
    ("madhyapradesh", "maize", "Kharif"): ("Mid-June to early July", "Mid-September to early November", 462),
    ("uttarpradesh", "maize", "Kharif"): ("Mid-June to mid-July", "Mid-September to mid-October", 463),
    ("tamilnadu", "maize", "Kharif"): ("Early June to mid-July", "October", 463),
    ("tamilnadu", "maize", "Rabi"): ("Early September to early October", "January", 463),
    ("punjab", "chickpea", "Rabi"): ("Mid-October to mid-November", "Mid-March to mid-April", 452),
    ("uttarpradesh", "chickpea", "Rabi"): ("Mid-October to mid-November", "Mid-March to mid-April", 452),
}


def public_guide(crop):
    return {key: value for key, value in GUIDES[crop].items() if key not in {"water_floor", "ph", "ph_limit"}}


def nutrient_summary(farm):
    if farm.nutrient_unit != "kg_ha":
        return [], "The report units do not support the available-nutrient screen. Ask your soil lab for elemental N, P and K in kg/ha."
    low = [name for name, limit in NUTRIENT_LIMITS.items() if getattr(farm, name) < limit]
    if low:
        return low, "Review low " + ", ".join(NAMES[name] for name in low) + " with your soil lab before buying fertilizer."
    return low, "None of the entered nutrients falls below the general soil-test screening thresholds."


def assess(crop, farm, production, climate_mm, low, state=None):
    guide = GUIDES[crop]
    reasons, cautions, severe = [], [], []
    if production and production["scope"] == "District":
        reasons.append("Recorded in your district in the selected season.")
    else:
        reasons.append("Recorded in your state in the selected season. District evidence is limited.")
        cautions.append("Confirm a locally suitable variety and sowing window.")
    screening_ph = guide.get("ph", (6.5, 7.5))
    if not guide.get("ph_limit", (5.0, 8.5))[0] <= farm.ph <= guide.get("ph_limit", (5.0, 8.5))[1]:
        severe.append("The soil pH falls outside the screening range. Review the soil test with your local KVK before planting.")
    elif screening_ph[0] <= farm.ph <= screening_ph[1]:
        reasons.append("The soil pH passes the reference screen.")
    else:
        cautions.append("The soil pH is outside the preferred reference range. Check local variety and soil advice.")
    if farm.soil_type == "Sandy" and crop == "rice":
        cautions.append("Sandy soil may make water control difficult in a transplanted lowland system.")
    if farm.soil_type == "Clay" and crop != "rice":
        cautions.append("Check field drainage before planting in clay soil.")
    if guide.get("water_floor") and farm.irrigation != "Irrigated":
        if farm.irrigation == "Rainfed" and (
            farm.season == "Zaid" or (climate_mm is not None and climate_mm < guide["water_floor"])
        ):
            severe.append("The stated water supply may be inadequate for this crop. Confirm supplemental irrigation.")
        else:
            cautions.append("Check that water is available through the key growth stages.")
    critical = set(low) - ({"n"} if crop not in {"rice", "maize"} else set())
    if critical:
        cautions.append("Make a soil-test nutrient plan for " + ", ".join(NAMES[key] for key in sorted(critical)) + ".")
    elif "n" in low:
        reasons.append("As a pulse, it can obtain some nitrogen through effective root nodulation. Confirm seed inoculation advice locally.")
    if farm.previous_crop.casefold() in {crop.casefold(), CROPS[crop][0].casefold()}:
        cautions.append("The same crop was grown last time. Check rotation and disease carry-over.")
    if farm.nutrient_unit != "kg_ha":
        cautions.append("Nutrient suitability needs a soil report on the supported testing basis.")
    level = "Low" if severe else "Moderate" if cautions else "High"
    result = {"category": level, "reasons": reasons, "cautions": severe + cautions,
              "soil": guide["soil"], "season": f"{farm.season} growing records apply. Confirm the district sowing window for your variety."}
    window = WINDOWS.get((state, crop, farm.season))
    if window:
        sowing, harvest, page = window
        result["calendar"] = {"sowing": sowing, "harvest": harvest, "source": f"{COST_SOURCE}#page={page}"}
    return result
