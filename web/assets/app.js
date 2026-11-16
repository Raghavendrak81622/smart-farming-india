const form = document.querySelector("#farm");
const output = document.querySelector("#results");
const status = document.querySelector("#request-status");
const pinStatus = document.querySelector("#pin-status");
const districtChoice = document.querySelector("#place-choice");
const districtSelect = form.elements.location_index;
const fmt = new Intl.NumberFormat("en-IN",{maximumFractionDigits:2});
const money = new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:0});
const shortDate = new Intl.DateTimeFormat("en-IN",{dateStyle:"medium",timeZone:"Asia/Kolkata"});
const dateTime = new Intl.DateTimeFormat("en-IN",{dateStyle:"medium",timeStyle:"short",timeZone:"Asia/Kolkata"});
const value = entry => entry == null ? "Unavailable" : fmt.format(entry);
const date = entry => shortDate.format(new Date(entry + "T00:00:00+05:30"));

function el(tag, content, css) {
  const element = document.createElement(tag);
  if (typeof content === "string") element.textContent = content;
  else if (content) element.append(...content);
  if (css) element.className = css;
  return element;
}
const note = words => el("p",words,"small");
const tile = (label, words) => el("div",[el("small",label),el("strong",words)],"tile");
function source(words, url) {
  const anchor = el("a",words);
  anchor.href = url;
  anchor.target = "_blank";
  anchor.rel = "noopener";
  return anchor;
}
function disclosure(title, content) {
  return el("details",[el("summary",title),...content],"details");
}
async function api(path, body) {
  const response = await fetch(path,body ? {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)} : undefined);
  const data = await response.json();
  if (!response.ok) {
    throw Error(Array.isArray(data.detail) ? data.detail.map(item=>item.loc.at(-1)+" "+item.msg).join(". ") : data.detail);
  }
  return data;
}

let resolvedPin = "";
form.elements.pin.addEventListener("input",()=>{
  districtChoice.hidden = true;
  resolvedPin = "";
  pinStatus.textContent = "";
});
form.elements.pin.addEventListener("change",()=>{
  if (form.elements.pin.validity.valid) lookup(form.elements.pin.value).catch(()=>{});
});
async function lookup(pin) {
  if (resolvedPin === pin) return;
  pinStatus.classList.remove("error");
  pinStatus.textContent = "Finding your district…";
  try {
    const result = await api("/api/pins/"+pin);
    if (form.elements.pin.value !== pin) return;
    districtSelect.replaceChildren(...result.locations.map((place,index)=>new Option(place.district+", "+place.state,index)));
    districtChoice.hidden = result.locations.length < 2;
    pinStatus.textContent = result.locations.length > 1 ? "This PIN serves more than one district." : districtSelect.options[0].text;
    resolvedPin = pin;
  } catch (error) {
    if (form.elements.pin.value === pin) {
      pinStatus.textContent = error.message;
      pinStatus.classList.add("error");
    }
    throw error;
  }
}

function weatherPanel(weather) {
  const card = el("section",[el("h2","Weather at your PIN")],"card");
  if (weather.reason) {
    card.append(note(weather.reason));
    return card;
  }
  card.append(note("Nearest forecast reading · "+value(weather.temperature)+" °C · "+value(weather.humidity)+"% humidity"),
    el("div",weather.days.map(day=>el("div",[
      el("small",date(day.date)),el("strong",value(day.min_c)+"–"+value(day.max_c)+" °C"),
      note(value(day.humidity)+"% average humidity"),
      note(day.rain_mm == null ? "Rain estimate unavailable" : value(day.rain_mm)+" mm forecast rain"),
    ],"tile")),"weather-grid"),
    el("p",["Forecast updated "+dateTime.format(new Date(weather.updated_at))+" IST · ",source("MET Norway",weather.source)],"small"));
  const rain = weather.days.filter(day=>day.rain_mm !== null).slice(0,2);
  if (rain.some(day=>day.rain_mm>0)) card.append(note("Rain is forecast. Check whether the field is workable before sowing or applying a treatment."));
  return card;
}
function finance(crop) {
  const quote = crop.market;
  const benchmark = crop.estimated_cost;
  const parts = [el("h3","Estimated expenses and profit")];
  if (!crop.price_calculation_available) {
    parts.push(note("The production source does not establish whether its rice amount is paddy or milled rice. A compatible cost and selling price cannot be matched."));
    return el("section",parts,"section");
  }
  if (quote) parts.push(note(quote.scope+" quote · "+quote.market+" · "+quote.commodity+" · "+quote.variety+" · "+quote.grade+" · "+date(quote.date)+" · "+value(quote.price)+" in source units"));
  else parts.push(note("There is no matching mandi quote for this crop in the local archive."));
  const price = el("input");
  Object.assign(price,{type:"number",min:"0",max:"1000000",step:"any",placeholder:"Confirm a local price"});
  const priceField = el("label",["Expected selling price (₹/quintal)",price],"price");
  const expense = el("input");
  Object.assign(expense,{type:"number",min:"0",max:"1000000000",step:"any",placeholder:"Optional"});
  const expenseField = el("label",["Your total cultivation cost (₹)",expense],"price");
  const totals = el("div",[],"figures");
  totals.setAttribute("aria-live","polite");
  const paint = ()=>{
    const rate = price.value !== "" && price.validity.valid ? Number(price.value) : null;
    const cost = expense.value !== "" ? (expense.validity.valid ? Number(expense.value) : null) : benchmark;
    const revenue = rate == null ? null : rate*crop.yield.tonnes*10;
    const profit = revenue == null || cost == null ? null : revenue-cost;
    const currency = amount=> amount == null ? "Unavailable" : money.format(amount);
    totals.replaceChildren(tile("Cultivation expenses",currency(cost)),tile("Expected revenue",currency(revenue)),tile("Estimated net profit",currency(profit)));
  };
  price.addEventListener("input",paint);
  expense.addEventListener("input",paint);
  paint();
  parts.push(totals,el("div",[priceField,expenseField],"fields two"));
  if (quote) {
    const confirm = el("button","Use quote after confirming ₹/quintal","quote-button");
    confirm.type = "button";
    confirm.addEventListener("click",()=>{price.value=quote.price; paint(); price.focus();});
    parts.push(confirm,note("The supplied archive has no unit column. Confirm the market unit or enter your own selling price."));
  }
  if (benchmark != null) parts.push(el("p",["Expense benchmark: "+money.format(crop.cost_rate)+"/quintal, 2024–25 all-India paid-out costs plus family labour. Your cost entry replaces this benchmark. ",source("CACP table 2.72",crop.cost_source)],"small"));
  else parts.push(note("Enter your total cultivation cost to estimate net profit. The published cost table has no matching crop and season benchmark."));
  return el("section",parts,"section");
}

function cropPanel(crop) {
  const harvest = crop.yield;
  const watch = disclosure("Pests, diseases and treatments",[
    note("Potential crop threats to scout for. Local outbreak likelihood is unavailable."),
    el("div",crop.watchlist.map(item=>el("div",[
      el("h4",item.name+" · "+item.kind),note(item.signs),
      el("p",[item.ipm+" ",source("Field guide",item.source)],"small")
    ])),"watch"),
    ...(crop.label_reference ? [el("p",[crop.label_reference.target+": "+crop.label_reference.name+". "+crop.label_reference.instructions+" ",
      source("PPQS product label",crop.label_reference.source)],"small")] : [note("Ask your local Krishi Vigyan Kendra for a verified crop- and pest-specific product if treatment is needed.")]),
    note(crop.safety)
  ]);
  return el("article",[
    el("div",[el("h2",crop.name),el("span",harvest.scope+" growing records","tag")],"summary"),
    note(crop.score == null ? "Model score unavailable" : "Reference match "+value(crop.score*100)+"%"),
    el("section",[el("h3","Expected harvest"),el("div",[
      tile("Total harvest",value(harvest.tonnes)+" t"),
      tile("Yield per hectare",value(harvest.tonnes_per_ha)+" t/ha"),
      tile("Historical range",harvest.range_tonnes.map(value).join("–")+" t")
    ],"figures"),el("p",[harvest.scope+" median from "+harvest.years.join(", ")+". Historical baseline; field outcomes vary. ",
      source("Crop statistics",harvest.source)],"small")],"section"),
    watch,finance(crop)
  ],"card");
}

form.addEventListener("submit",async event=>{
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  status.classList.remove("error");
  status.textContent = "Checking weather, crop and market records…";
  output.replaceChildren();
  try {
    const pin = form.elements.pin.value;
    const hadLocation = resolvedPin === pin;
    await lookup(pin);
    if (!hadLocation && !districtChoice.hidden) {
      districtSelect.focus();
      status.textContent = "Choose your district, then compare crops.";
      return;
    }
    const fields = new FormData(form);
    const numberOrNull = key=>fields.get(key)==="" ? null : Number(fields.get(key));
    const result = await api("/api/recommend",{
      pin,location_index:Number(fields.get("location_index")),acres:Number(fields.get("acres")),
      ph:Number(fields.get("ph")),n:numberOrNull("n"),p:numberOrNull("p"),k:numberOrNull("k"),
      source_scale:fields.has("source_scale")
    });
    const headline = el("h2",result.location.district+", "+result.location.state);
    headline.tabIndex = -1;
    output.append(el("div",[headline,note(result.season+" season · "+value(result.acres)+" acres ("+value(result.hectares)+" ha)")],"result-head"),
      weatherPanel(result.weather),el("section",[
        el("h2","Crop recommendations"),note(result.model_note),
        note("Soil report · pH "+value(result.soil.ph)+" · N "+value(result.soil.n)+" · P "+value(result.soil.p)+" · K "+value(result.soil.k)),
        note("Prioritised by documented local growing history and model match. Forecast rain is shown separately for field timing.")
      ],"card"));
    if (result.crops.length) output.append(...result.crops.map(cropPanel));
    else output.append(el("p","There are too few recent, compatible crop seasons in the district or state records to suggest a crop with a harvest estimate.","card"));
    status.textContent = "";
    headline.focus();
  } catch (error) {
    status.classList.add("error");
    status.textContent = error.message || "The recommendation could not be completed.";
  } finally {
    button.disabled = false;
  }
});
