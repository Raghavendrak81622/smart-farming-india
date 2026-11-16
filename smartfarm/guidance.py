"""Crop watchlists and treatment references. No local outbreak model is implied."""

RICE = "https://niphm.gov.in/IPMPackages/Rice.pdf"
MAIZE = "https://www.ppqs.gov.in/sites/default/files/faw_do.pdf"
CHICKPEA = "https://niphm.gov.in/IPMPackages/Chickpea.pdf"
PIGEON = "https://agritech.tnau.ac.in/crop_protection/crop_pdf/Pigeonpea.pdf"
PULSES = "https://agritech.tnau.ac.in/org_farm/orgfarm_agridiseases.html"
RICE_LABEL = "https://ppqs.gov.in/sites/default/files/cartap_hydrochloride_75_sg93fdhanuka_agritech_limited_1.pdf"
PULSE_LABEL = "https://ppqs.gov.in/sites/default/files/spinetoram_11.7_1-merged.pdf"

WATCH = {
    "rice": [
        ("Yellow stem borer", "Pest", "Scout tillering rice for drying centre shoots and flowering rice for white, unfilled heads.",
         "Inspect for egg masses and verify the pest before deciding on treatment.", RICE),
        ("Rice blast", "Disease", "Check leaves for pale-centred lesions with darker margins and the panicle neck for dark infection.",
         "Use healthy seed and a locally suitable resistant variety. Have suspect symptoms confirmed.", RICE),
    ],
    "maize": [
        ("Fall armyworm", "Pest", "From emergence, check whorls for fresh feeding holes, frass and larvae.",
         "Start field scouting at emergence. PPQS advises against chemical sprays for fall armyworm from tasselling onward.", MAIZE),
        ("Post-flowering stalk rot", "Disease", "Check for weakening stalks or lodging after flowering.",
         "Use rotation and avoid crop moisture stress at flowering. Confirm the cause of lodging before treatment.",
         "https://agritech.tnau.ac.in/pdf/8.pdf"),
    ],
    "chickpea": [
        ("Gram pod borer", "Pest", "Inspect foliage, flowers and pods for larvae and feeding holes.",
         "Scout for eggs and small larvae before pod damage increases. Preserve natural enemies.", CHICKPEA),
        ("Wilt and root rot", "Disease", "Inspect wilting or dying plants and their roots, especially early in crop growth.",
         "Use crop rotation and locally recommended resistant varieties. Confirm the diagnosis.", CHICKPEA),
    ],
    "pigeonpeas": [
        ("Pod borers", "Pest", "Inspect flowers and young pods for larvae and entry holes.",
         "Use trap catches as a signal to inspect the plants. Base treatment on confirmed field counts.", PIGEON),
        ("Fusarium wilt", "Disease", "Look for wilting patches and darkened tissue towards the stem base.",
         "Use locally suitable resistant varieties and rotation in fields with a wilt history.", PIGEON),
    ],
    "mungbean": [
        ("Whitefly", "Pest", "Check the leaf undersides and look for yellow mosaic symptoms.",
         "Monitor young growth and use varieties recommended locally for yellow mosaic resistance.", PULSES),
        ("Yellow mosaic", "Disease", "Look for yellow mosaic patches on leaves. Whiteflies can carry the virus.",
         "Use resistant varieties and confirm the symptoms before treating a suspected vector.", PULSES),
    ],
    "blackgram": [
        ("Whitefly", "Pest", "Check leaf undersides for whiteflies and inspect new leaves for mottling.",
         "Monitor emerging plants and ask about locally suitable yellow mosaic-resistant varieties.", PULSES),
        ("Yellow mosaic", "Disease", "Look for patchy yellowing on leaves and verify that the cause is yellow mosaic.",
         "Use locally suitable resistant varieties. Consult an extension officer on vector management.", PULSES),
    ],
}

RICE_TREATMENT = {
    "name": "Cartap hydrochloride 75% SG",
    "target": "Yellow stem borer in rice",
    "instructions": "A PPQS-hosted label for this formulation lists a knapsack or equivalent calibrated sprayer and a 48-hour re-entry interval. Confirm current registration and the exact formulation, dose and harvest interval on the pack with a Krishi Vigyan Kendra before use.",
    "source": RICE_LABEL,
}

def pod_borer_label(crop, interval):
    return {
        "name": "Spinetoram 11.7% w/w SC",
        "target": "Confirmed gram pod borer in " + crop,
        "instructions": (
            f"The PPQS label indicates 24-hour re-entry and a {interval}-day pre-harvest interval. "
            "Use a calibrated foliar sprayer only after a local adviser confirms treatment is needed. "
            "Check the current pack label for the rate and verify crop and pest applicability. "
            "Follow the label’s protective clothing requirements and avoid spraying near water or while bees forage."
        ),
        "source": PULSE_LABEL,
    }

LABELS = {"rice": RICE_TREATMENT, "chickpea": pod_borer_label("chickpea", 20),
          "pigeonpeas": pod_borer_label("pigeon pea", 23)}


def guidance(crop):
    return {
        "watchlist": [{"name": name, "kind": kind, "signs": signs, "ipm": ipm, "source": source}
                      for name, kind, signs, ipm, source in WATCH[crop]],
        "label_reference": LABELS.get(crop),
        "safety": "Use the product label’s protective equipment, re-entry and harvest instructions. Consult a Krishi Vigyan Kendra or agricultural officer before choosing a pesticide.",
    }
