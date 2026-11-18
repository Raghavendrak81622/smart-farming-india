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

ARCHIVED_LABELS = {"rice": RICE_LABEL, "chickpea": PULSE_LABEL, "pigeonpeas": PULSE_LABEL}

FIELD_DETAILS = {
    "Yellow stem borer": ("Nursery, tillering and heading", "Watch the growing point and developing heads during susceptible stages.", "Check several parts of the field for egg masses, dead hearts and white heads.", "stem-borer"),
    "Rice blast": ("Vegetative growth to heading", "Leaf wetness and susceptible varieties favour infection.", "Inspect leaf lesions and the neck beneath emerging heads.", "rice-blast"),
    "Fall armyworm": ("Seedlings and whorl stage", "Young maize with fresh whorl feeding needs close inspection.", "Open the whorl and confirm fresh frass and live larvae before treatment.", "fall-armyworm"),
    "Post-flowering stalk rot": ("After flowering", "Stress around flowering can predispose the crop.", "Check for soft stalks or lodging in affected patches.", None),
    "Gram pod borer": ("Flowering and pod formation", "Tender flowers and developing pods provide feeding sites.", "Check plants for eggs, caterpillars and holes in pods.", "pod-borer"),
    "Wilt and root rot": ("Seedling to vegetative growth", "Fields with recurring wilt need particular attention.", "Inspect the roots and stem of affected plants, then seek a diagnosis.", None),
    "Pod borers": ("Flowering and pod development", "Flowers and young pods are vulnerable to several species.", "Inspect flower clusters and pods. Confirm the species before selecting control.", None),
    "Fusarium wilt": ("Vegetative growth onward", "Repeated pigeon pea in the same field increases concern where wilt has occurred.", "Check wilted plants in patches and inspect stem tissue near the soil line.", None),
    "Whitefly": ("Early leaf growth onward", "Whiteflies can carry yellow mosaic virus.", "Turn leaves over and inspect new growth and field edges.", "whitefly"),
    "Yellow mosaic": ("Early leaf growth onward", "Whitefly movement can spread the disease.", "Check new leaves for yellow mosaic and confirm the diagnosis.", None),
}


def guidance(crop):
    threats = []
    for name, kind, signs, ipm, source in WATCH[crop]:
        stage, conditions, monitoring, image = FIELD_DETAILS[name]
        threats.append({
            "name": name, "kind": kind, "signs": signs, "ipm": ipm, "source": source,
            "stage": stage, "conditions": conditions, "monitoring": monitoring, "image": image,
        })
    return {
        "watchlist": threats,
        "threat_evidence": "Common crop threats. Regional surveillance and current outbreak status are unavailable.",
        "label_reference": ARCHIVED_LABELS.get(crop),
        "safety": "Current registration and the exact crop–pest label could not be verified. Consult your local Krishi Vigyan Kendra or agricultural officer. Follow the current label for protective equipment, re-entry and harvest intervals.",
    }
