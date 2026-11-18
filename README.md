# Fieldwise · Smart Farming India

Fieldwise uses local postal, production and agronomy references to compare crops and estimate harvest and returns. Farm plans and soil reports stay on the device. Climate inputs stay on the server and are excluded from recommendation responses and saved plans.

## Run on Windows 11

From the project folder, run `.\Start-Farming.ps1` and open [Fieldwise](http://127.0.0.1:8000/). To make a fresh Python 3.12 environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\Start-Farming.ps1 prepare
.\Start-Farming.ps1
```

Keep the local datasets in the locations below. Run `prepare` while the server is stopped. The existing Codex-bundled environment and .NET-independent Windows OCR implementation were tested. Fresh Windows installs need a Windows OCR language, such as English, in Language settings. PDFs with usable text do not need Windows OCR. The app manual form remains available if report extraction fails. Python only processes the first three PDF pages and caps uploads at 8 MB. Verify extracted values and choose the appropriate nutrient units.

## Farmer workflow

Enter a PIN, acreage, season, pH, nutrients and water access. Where a PIN crosses districts, select one. Fieldwise screens for each supported crop’s selected-season district or state evidence, soil pH, tested nutrients, water access, soil type and repeat-crop caution. Its High, Moderate and Low categories are rules-based screens. A High result means no screening caution was triggered. It does not replace local variety or field advice. Fieldwise shows up to five matches, with fewer where the data does not support more.

Open the cultivation and crop protection guides for the source-based methods. References state their scope, and the app labels the pest watchlist as common threats without local outbreak confirmation. Current pesticide registration and label applicability could not be verified from the available records. The app offers IPM and directs farmers to their local KVK or agricultural officer for chemical selection. Crop photos and available identification photos have individual source and licence credits.

Conservative, average and optimistic yields use the minimum, arithmetic mean and maximum of up to five annual yields for the crop, season and geography. Fieldwise applies the yield per hectare to acreage after conversion (one acre = 0.40468564224 ha and one tonne = 10 quintals). The average historical district estimate had a latest-year holdout MAE of 0.303 t/ha across 4,906 series with sufficient records. Records end in 2022 and the historical range is not a prediction interval. Rice harvest retains the source’s unspecified rice basis, so rice revenue is withheld.

Price and total costs stay fixed across the three yield scenarios. Confirm the selling price in ₹/quintal. Fieldwise calculates revenue as quintals × price and profit as revenue less whole-farm cost. A matching 2024–25 CACP A2+FL benchmark multiplied by the average harvest supplies a default where available. It covers paid costs and family labour and is a national historical benchmark. Enter a farm total or complete itemised budget to override it. A partial breakdown remains a subtotal. Save a plan explicitly to retain its input, estimates and budget in `data/fieldwise-plans.sqlite`. Back up that file to keep your plans.

## Data audit

| Source | Coverage and limitations |
|---|---|
| `Crop_recommendation.csv` | 2,200 rows, 22 crop labels, no missing cells, no dated or geographic labels, and no verified NPK units or rainfall accumulation interval. The six-crop legacy classifiers were evaluated on 120 stratified holdout rows. The pH-only variant scored 32.5% on that dataset. The other variant scores measure the source distribution and do not validate field suitability. Models remain local research artifacts and are not loaded by the app. |
| `archive (2).zip` | A single duplicate crop CSV. Excluded. |
| `archive.zip` | PlantVillage image archive, 41,278 entries including repeated image trees. It lacks district and collection dates. It cannot establish outbreak risk and is excluded from recommendations. |
| `archive (1).zip` | Mandi quotes in overlapping annual CSV and Parquet representations, with date, state, district, market, crop, variety, grade and quote values. Fieldwise streams the 2026 CSV partition rather than processing both formats. The supplied files do not state the currency or weight basis. |
| `9ef84268-d588-465a-a308-a864a43d0070.csv` | 9,585 rows across 24 state labels, no missing cells and all dated 16 November 2026. The file has no price unit column. Quotes are shown as archive evidence and cannot automatically populate the profit calculation. |
| `RFone_imd_rf_1x1_*.nc` | Six nonempty IMD 1° daily rainfall files for 2020–2025, in mm. Two empty selection files are skipped. Negative fill values and incomplete seasons are excluded. Seasonal grid averages require at least three complete years. They inform a conservative water-access check for paddy/maize. A missing local grid leaves rainfall out of the screen. |
| `sources/pins.csv` | Public India Post directory mirror. 157,126 office rows, 36 state/territory labels and 19,300 distinct supplied PINs. About 8,800 entries are missing one or both coordinates. A known test office is excluded. Coordinates approximate the postal area and do not identify individual farms. |
| `sources/production.csv` | Mirrored government area/production statistics, 407,315 rows across 34 supplied state labels, 1997–2022. Production is missing in 4,973 rows. Fieldwise uses the six supported crops, matching seasons, positive area and production, and plausibility screening. No variety-specific yield is available. |
| CACP and agronomy references | National crop/season cost benchmarks and source-specific crop methods. District input costs are absent. Soil ratings are used only for available elemental nutrient values in kg/ha. |

Kharif uses June–September, Rabi October–February across years, and Zaid March–May for the internal rainfall screen. The APY Summer category maps to Zaid. The annual season records and coarse rainfall grid do not resolve exact village sowing dates. [Soil testing manual](https://soilhealth.dac.gov.in/files/Manual/14072023Manual_Class_9_10.pdf) · [Crop water benchmarks](https://www.fao.org/4/s2022e/s2022e02.htm) · [CACP cost table 2.72](https://nccd.gov.in/uploads/Agricultural_Statisitcs_at_a_Glance_2024_25_11da3cd37d.pdf)

### Data setup for a fresh clone

Place the original crop CSV, two market sources and the IMD NetCDF files at the project root as named above. Copy the [India Post directory mirror](https://raw.githubusercontent.com/dropdevrahul/pincodes-india/master/pincode.csv) to `sources/pins.csv` and the [production mirror](https://raw.githubusercontent.com/Ankush-Manhas840/crop-yield-prediction/master/data/crop_production.csv) to `sources/production.csv`. Run `prepare` to refresh the ignored cache and validation report. User data, generated evidence and datasets stay local. [Government APY reports](https://data.desagri.gov.in/website/crops-apy-report-web)

If you acquire a unit-confirmed official market extract, import it as `sources/verified_prices.csv` with `State,District,Market,Commodity,Variety,Grade,Arrival_Date,Modal_Price,unit,source`. Dates use YYYY-MM-DD, unit must be `INR/quintal` and source must link to the corresponding government report. Validate the quote and crop basis before importing. Quotes older than 30 days require a manual selling-price entry.
