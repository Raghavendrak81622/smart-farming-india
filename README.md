# Smart Farming India

A single local web page for crop recommendations, PIN-area forecasts, crop threats and treatments, expected harvest and estimated profit.

## Run

From this folder in PowerShell, run `.\Start-Farming.ps1`, then open [the app](http://127.0.0.1:8000/). The generated data and models in `cache` are ready to use. The launcher uses a local virtual environment or the available Codex bundled Python. To install in a fresh Python 3.12 environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\Start-Farming.ps1 prepare
.\Start-Farming.ps1
```

### Data for a fresh clone

Place your original `Crop_recommendation.csv`, `archive (1).zip` (with member `csv/2026.csv`), and `9ef84268-d588-465a-a308-a864a43d0070.csv` at the project root. Save the public [postal directory CSV](https://raw.githubusercontent.com/dropdevrahul/pincodes-india/master/pincode.csv) as `sources/pins.csv` and the [district crop production CSV](https://raw.githubusercontent.com/Ankush-Manhas840/crop-yield-prediction/master/data/crop_production.csv) as `sources/production.csv`. Then run `prepare` to generate the local lookup and models. The repository tracks app source only.

Live weather needs internet access. The app sends approximate postal-area coordinates to MET Norway. Soil values, acreage and selling prices are kept local. If weather is unavailable, recommendations fall back to soil measurements and regional crop records. To deploy or distribute, review the weather provider's terms and set `SMARTFARM_WEATHER_USER_AGENT` to an identifying application string with your contact URL or email. [MET Norway forecast documentation](https://api.met.no/weatherapi/locationforecast/2.0/documentation) · [Weather service terms](https://api.met.no/doc/TermsOfService)

## How the estimates work

- **PIN and season.** The local PIN file is a mirror of the India Post directory. A PIN can serve multiple districts. Forecasts use median office coordinates for the selected district. Kharif, Rabi and summer are inferred from the current India month as broad planning seasons. Historical production evidence determines which crops have been grown in that season. [India Post source mirror](https://github.com/dropdevrahul/pincodes-india)
- **Crop recommendation.** Four newly trained random-forest variants use pH, optionally comparable NPK measurements, and, when available, near-term forecast temperature and humidity. Forecast rain informs planting and treatment timing. The crop file does not document the rainfall window or NPK units. Ordinary laboratory NPK measurements are displayed without using them as training-scale values. Scores are exploratory reference matches.
- **Yield.** Uses the median of up to five recorded seasonal district yields, with a labelled state fallback. At least three distinct seasons and an observation from 2018 or later are required. Acres convert to hectares, and the median yield scales to land area. Training coverage is limited to six crops with matching evidence. The chronological test of the district median reported 0.303 tonnes per hectare MAE across 4,906 groups. Source records end in 2022. [Government APY reports](https://data.desagri.gov.in/website/crops-apy-report-web) · [Data mirror](https://github.com/Ankush-Manhas840/crop-yield-prediction)
- **Pests and treatments.** Crop watchlists and management notes use field references. District outbreak probabilities need surveillance data. Chemical references are crop and pest specific and link to published labels. Have the current pack label and field diagnosis verified before treatment. [PPQS maize fall armyworm guide](https://www.ppqs.gov.in/sites/default/files/faw_do.pdf) · [NIPHM chickpea IPM guide](https://niphm.gov.in/IPMPackages/Chickpea.pdf)
- **Profit.** For compatible crops, the app multiplies expected quintals by a confirmed selling price and subtracts the expense estimate. The local archive quote files omit the unit, so confirm ₹/quintal or enter a local price. Estimated expenses use the 2024–25 all-India A2+FL benchmark for the published crop and season. Farmer-entered total cost can replace the benchmark. Rice finance is withheld because the production file does not establish the paddy/milled basis. Figures are planning scenarios. [CACP table 2.72](https://nccd.gov.in/uploads/Agricultural_Statisitcs_at_a_Glance_2024_25_11da3cd37d.pdf)

Original uploaded CSV, ZIP and NetCDF files remain in the project root. The rebuilt app does not load the previous app or write a farm history. The previous activity database was retained because it contains saved plans.
