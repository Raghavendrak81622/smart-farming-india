"""Supported crops and provenance for harvest and finance scenarios."""

CROPS = {
    "rice": ("Rice / paddy", "Rice", ("Paddy(Dhan)(Common)", "Paddy (Common)"), "Kharif", 1533),
    "maize": ("Maize", "Maize", ("Maize",), "Kharif", 1447),
    "chickpea": ("Chickpea", "Gram", ("Bengal Gram (Gram)(Whole)",), "Rabi", 3527),
    "pigeonpeas": ("Pigeon pea", "Arhar/Tur", ("Arhar (Tur/Red Gram)(Whole)", "Red Gram"), "Kharif", 4761),
    "mungbean": ("Green gram", "Moong(Green Gram)", ("Green Gram (Moong)(Whole)",), "Kharif", 5788),
    "blackgram": ("Black gram", "Urad", ("Black Gram (Urd Beans)(Whole)",), "Kharif", 4883),
}

COST_SOURCE = "https://nccd.gov.in/uploads/Agricultural_Statisitcs_at_a_Glance_2024_25_11da3cd37d.pdf"
YIELD_SOURCE = "https://data.desagri.gov.in/website/crops-apy-report-web"
ACRE_TO_HA = 0.40468564224


def location_key(value):
    value = "".join(ch for ch in value.casefold() if ch.isalnum())
    return {
        "orissa": "odisha", "uttaranchal": "uttarakhand", "uttrakhand": "uttarakhand",
        "chattisgarh": "chhattisgarh", "bangalore": "bengaluruurban", "bangaloreurban": "bengaluruurban",
        "bangalorerural": "bengalururural", "anantapur": "ananthapuramu", "anantapuramu": "ananthapuramu",
        "nasik": "nashik", "puducherry": "pondicherry", "belgaum": "belagavi",
        "mysore": "mysuru", "gulbarga": "kalaburagi", "bangaloresouth": "bengalurusouth",
    }.get(value, value)
