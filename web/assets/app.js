const form = document.querySelector("#farm");
const output = document.querySelector("#results");
const status = document.querySelector("#request-status");
const pinStatus = document.querySelector("#pin-status");
const districtChoice = document.querySelector("#place-choice");
const districtSelect = form.elements.location_index;
const fmt = new Intl.NumberFormat("en-IN",{maximumFractionDigits:2});
const money = new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:0});
const shortDate = new Intl.DateTimeFormat("en-IN",{dateStyle:"medium",timeZone:"Asia/Kolkata"});
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
  const response = await fetch(path,body instanceof File ? {method:"POST",body} : body ? {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)} : undefined);
  const data = await response.json().catch(()=>({detail:"The request could not be completed. Try again."}));
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


const costNames = {land:"Land preparation",seed:"Seed",fertilizer:"Fertilizer",protection:"Crop protection",irrigation:"Irrigation",
  labour:"Labour",machinery:"Machinery",harvest:"Harvesting",transport:"Transport",other:"Other expenses"};
const scenarioNames = {conservative:"Conservative",average:"Average",optimistic:"Optimistic"};
const credits = fetch("/assets/photos/credits.json").then(r=>r.ok?r.json():{}).catch(()=>({}));
const currency = amount => amount == null ? "Unavailable" : money.format(amount);
let plan;
let budgets = {};

function table(headers, rows) {
  return el("div",[el("table",[
    el("thead",[el("tr",headers.map(name=>el("th",name)))]),
    el("tbody",rows.map(row=>el("tr",row.map((v,index)=>el(index===0?"th":"td",v)))))
  ])],"table-wrap");
}
function photo(key, alt, media, crop=false) {
  if (!media[key]) return [];
  const image = el("img");
  Object.assign(image,{src:"/assets/photos/"+key+".webp",alt,loading:"lazy",width:crop?260:160,height:crop?164:116});
  return [el("figure",[image,el("figcaption",[source(media[key].author,media[key].source)," · ",
    ...(media[key].license_url ? [source(media[key].license,media[key].license_url)] : [media[key].license])," · resized"])],crop?"crop-photo":"threat-photo")];
}
function description(name, words) {
  return el("p",[el("strong",name+" "),words],"small");
}

function cropGuide(crop, season) {
  const g = crop.guide;
  const calendar = crop.suitability?.calendar;
  return disclosure("Cultivation guide",[
    note("Reference methods and varieties. Confirm the package for your district and planting system before buying inputs."),
    ...(season ? [description("Sowing window",crop.suitability.season)] : []),
    ...(calendar ? [description("State reference sowing window",calendar.sowing),
      description("State reference harvesting window",calendar.harvest),
      el("p",[source("ICAR crop calendar",calendar.source)],"small")] : []),
    description("Land preparation",g.land),description("Seed per acre",g.seed),
    description("Sowing and spacing",g.sow),
    description("Fertilizer","Use your Soil Health Card and the local variety package to set fertilizer quantities. The screening result does not prescribe rates."),
    description("Irrigation",g.irrigation),description("Duration",g.duration),
    description("Harvest",g.harvest),
    ...(crop.suitability?.cautions || []).map(words=>description("Precaution",words)),
    el("p",[source("Cultivation reference",g.source),...(g.soil_source?[" · ",source("Soil reference",g.soil_source)]:[])],"small")
  ]);
}
function protection(crop,media) {
  return disclosure("Pest and disease protection",[
    note(crop.threat_evidence),
    ...crop.watchlist.map(item=>el("div",[
      el("h4",item.name+" · "+item.kind),...photo(item.image,item.name,media),
      description("Symptoms",item.signs),description("Stage",item.stage),description("Conditions",item.conditions),
      description("Monitoring",item.monitoring),description("Prevention and management",item.ipm),
      el("p",[source("Field guide",item.source)],"small")
    ],"threat")),
    el("h4","Pesticide guidance"),
    note(crop.safety),...(crop.label_reference?[el("p",[source("Archived PPQS label for discussion with your adviser",crop.label_reference)],"small")]:[]),
  ]);
}
function marketText(quote) {
  if (!quote) return "No matching local or state quote.";
  const amount = quote.verified ? currency(quote.price)+"/quintal" : value(quote.price)+" reported, unit unavailable";
  return quote.scope+" · "+quote.market+" · "+quote.commodity+" · "+quote.variety+" · "+quote.grade+" · "+date(quote.date)+" · "+amount+(quoteIsOld(quote)?" · older than 30 days":"");
}
function quoteIsOld(quote) {
  const day = 24*60*60*1000;
  const indiaOffset = 330*60*1000;
  const quoteDay = new Date(quote.date+"T00:00:00+05:30").getTime();
  const today = Math.floor((Date.now()+indiaOffset)/day)*day-indiaOffset;
  return quote.stale || today-quoteDay > 30*day;
}
function estimate(crop, budget = {}) {
  const quote = crop.market;
  const defaultPrice = quote?.verified && !quoteIsOld(quote) ? quote.price : null;
  const price = budget.price ?? defaultPrice;
  const entries = Object.values(budget.items || {});
  const subtotal = entries.length ? entries.reduce((total,v)=>total+v,0) : null;
  const cost = budget.total ?? (budget.use_items && subtotal != null ? subtotal : crop.estimated_cost);
  const scenarios = Object.entries(crop.yield.scenarios).map(([key,harvest])=>{
    const revenue = crop.price_calculation_available && price != null ? price*harvest.quintals : null;
    return {key, ...harvest, revenue, profit: revenue != null && cost != null ? revenue-cost : null};
  });
  return {price, defaultPrice, cost, subtotal, scenarios};
}
function amountField(label, amount, max, onChange, placeholder="") {
  const input = el("input");
  Object.assign(input,{type:"number",min:0,max,step:"any",value:amount??"",placeholder});
  input.addEventListener("input",()=>onChange(input.value!=="" && input.validity.valid ? Number(input.value) : null));
  return el("label",[label,input]);
}
function comparison(plan, target) {
  const rows = plan.crops.map(crop=>{
    const budget = budgets[crop.crop] || {};
    return [crop,budget,estimate(crop,budget)];
  });
  const metric = (name, getter) => [name,...rows.map(([c,b,e])=>getter(c,b,e))];
  target.replaceChildren(el("h2","Compare crops"),table(["Measure",...plan.crops.map(c=>c.name)],[
    metric("Suitability",c=>c.suitability.category),
    metric("Crop duration",c=>c.guide.duration),
    metric("Water needs",c=>c.guide.water),
    metric("Average harvest",c=>value(c.yield.scenarios.average.quintals)+" q"),
    metric("Seed cost",(_,b)=>currency(b.items?.seed)),
    metric("Cultivation cost",(_,__,e)=>currency(e.cost)),
    metric("Average revenue",(_,__,e)=>currency(e.scenarios[1].revenue)),
    metric("Average profit",(_,__,e)=>currency(e.scenarios[1].profit)),
    metric("Main risks",c=>c.suitability.cautions[0] || c.watchlist[0]?.name || "Confirm field conditions"),
  ]));
}
function finances(crop, refreshComparison) {
  const budget = budgets[crop.crop] ||= {items:{},use_items:false};
  const breakdown = el("p");
  const figures = el("div");
  const repaint = ()=>{
    const e = estimate(crop,budget);
    breakdown.textContent = (e.subtotal == null ? "No itemised costs entered." : "Subtotal of entered items: "+currency(e.subtotal))+
      " Total used: "+currency(e.cost)+".";
    figures.replaceChildren(table(["Scenario","Yield (q/acre)","Harvest (q)","Expenses","Revenue","Net profit"],
      e.scenarios.map(row=>[scenarioNames[row.key],value(row.quintals_per_acre),value(row.quintals),currency(e.cost),currency(row.revenue),currency(row.profit)])));
    refreshComparison();
  };
  const parts = [el("h3","Harvest, expenses and returns"),
    note(crop.yield.scope+" records · "+crop.yield.years.join(", ")+" · "+crop.yield.basis),
    note("Scenarios use the lowest, average and highest observed annual yields. Price and expenses are held constant across all three."),
    note(marketText(crop.market)),
    ...(crop.market?.source ? [el("p",[source("Official market report",crop.market.source)],"small")] : [])];
  const harvest = crop.yield.scenarios;
  const chart = el("div",Object.entries(harvest).map(([key,row])=>{
    const meter = el("meter");
    Object.assign(meter,{min:0,max:harvest.optimistic.quintals,value:row.quintals});
    meter.setAttribute("aria-label",scenarioNames[key]+" estimated harvest");
    return el("div",[el("span",scenarioNames[key]),meter,el("strong",value(row.quintals)+" q")]);
  }),"harvest-bars");
  parts.push(chart);
  if (crop.price_calculation_available) {
    const priceHint = estimate(crop,budget).defaultPrice;
    parts.push(el("div",[
      amountField("Selling price (₹/quintal)",budget.price,1e6,v=>{budget.price=v;repaint()},priceHint==null?"Enter local price":value(priceHint)),
      amountField("Total costs for your land (₹)",budget.total,1e9,v=>{budget.total=v;repaint()},"Optional override")
    ],"fields two finance-fields"));
    if (priceHint == null) parts.push(note("Enter a confirmed selling price. Unverified or older quotes are excluded from calculations."));
  } else parts.push(note("Revenue is unavailable until the production and selling price use the same rice product basis."));
  const use = el("input");
  use.type="checkbox"; use.checked=budget.use_items;
  use.addEventListener("change",()=>{budget.use_items=use.checked;repaint()});
  parts.push(disclosure("Cultivation expense breakdown",[
    note("Enter costs in rupees for the whole area. Missing items are counted as zero only if you mark the breakdown complete."),
    el("div",Object.entries(costNames).map(([key,label])=>amountField(label+" (₹)",budget.items[key],1e9,v=>{
      if(v==null) delete budget.items[key];else budget.items[key]=v;
      repaint();
    })),"fields three"),
    el("label",[use," Use this complete breakdown as the total"],"choice"),
    breakdown,
  ]));
  if (crop.estimated_cost != null) parts.push(el("p",[
    "Default expense uses the average harvest × the national "+currency(crop.cost_rate)+"/quintal benchmark for 2024–25, covering paid costs and family labour. A complete breakdown or total replaces it. ",
    source("CACP benchmark",crop.cost_source)],"small"));
  else parts.push(note("A matching cultivation cost benchmark is unavailable. Enter your own total or complete breakdown."));
  parts.push(figures);
  repaint();
  return el("section",parts,"section");
}

async function renderPlan(next) {
  plan = next;
  budgets = structuredClone(next.budgets);
  const media = await credits;
  const farm = next.farm;
  const summary = el("h1","Your farming plan");
  summary.tabIndex=-1;
  const saveStatus=note("");
  saveStatus.setAttribute("role","status");
  const save = el("button","Save plan");
  save.disabled = !next.crops.length;
  save.addEventListener("click",async ()=>{
    save.disabled=true;
    try {await api("/api/plans",{id:next.id,budgets});saveStatus.textContent="Saved on this device."}
    catch(error){saveStatus.textContent=error.message}
    finally{save.disabled=false}
  });
  const compare = el("section",[],"card");
  const refresh = ()=>comparison(next,compare);
  const sections = [el("header",[summary],"page-title"),
    el("section",[el("h2",next.location.district+", "+next.location.state),
      note(next.season+" · "+value(next.acres)+" acres · "+farm.irrigation+" · PIN "+farm.pin),
      note("Soil "+farm.soil_type.toLowerCase()+" · pH "+value(farm.ph)+" · N "+value(farm.n)+" · P "+value(farm.p)+" · K "+value(farm.k)),
      note(next.soil_note),save,saveStatus],"card farm-summary")];
  if (!next.crops.length) sections.push(el("section",[el("h2","Crop recommendations"),note("There is too little matching crop evidence for this region and season.")],"card"));
  else {
    sections.push(el("header",[el("h2","Recommended crops"),note("Suitability considers local season records, your soil and your water access. A Low rating means check the identified constraints before planting.")]));
    for (const crop of next.crops) {
      const s=crop.suitability;
      sections.push(el("article",[
        el("div",[...photo(crop.crop,crop.name,media,true),el("div",[
          el("div",[el("h2",crop.name),el("span",s.category+" suitability","tag "+s.category.toLowerCase())],"summary"),
          ...s.reasons.map(note),...s.cautions.map(words=>description("Check",words)),
          description("Soil",s.soil),description("Season",s.season),
          description("Water",crop.guide.water),description("Duration",crop.guide.duration)
        ])],"crop-overview"),
        cropGuide(crop,next.season),protection(crop,media),finances(crop,refresh)
      ],"card"));
    }
    sections.push(compare);
  }
  output.replaceChildren(...sections);
}

const upload = document.querySelector("#soil-upload");
upload.addEventListener("change",async ()=>{
  if (!upload.files.length)return;
  const file = upload.files[0];
  const feedback=document.querySelector("#soil-status");
  if (file.size>8*1024*1024) {feedback.textContent="Choose a file under 8 MB.";return}
  feedback.textContent="Reading the soil report…";
  try{
    const result=await api("/api/soil-report",file);
    if(upload.files[0]!==file)return;
    for(const [field,reading] of Object.entries(result.readings)) form.elements[field].value=reading;
    form.elements.nutrient_unit.value="other";
    feedback.textContent="Check the extracted readings and select the nutrient units from your report before submitting.";
  }catch(error){if(upload.files[0]===file)feedback.textContent=error.message}
});

form.addEventListener("submit",async event=>{
  event.preventDefault();
  const button=form.querySelector("button");
  button.disabled=true;
  status.textContent="Checking your farm details…";
  status.classList.remove("error");
  try {
    const pin=form.elements.pin.value;
    const lookedUp=resolvedPin===pin;
    await lookup(pin);
    if (!lookedUp && !districtChoice.hidden) {
      districtSelect.focus();status.textContent="Choose your district, then compare crops.";return;
    }
    const values=Object.fromEntries(new FormData(form));
    for(const name of ["acres","ph","n","p","k","location_index"]) values[name]=Number(values[name]);
    await renderPlan(await api("/api/recommend",values));
    status.textContent="";
    location.hash="results";
  } catch(error) {status.classList.add("error");status.textContent=error.message}
  finally {button.disabled=false}
});

async function savedPage(view) {
  const entries = await api("/api/plans");
  const rows=entries.map(entry=>{
    const open=el("button","Open "+entry.district+" plan");
    open.addEventListener("click",async ()=>{
      open.disabled=true;
      try{await renderPlan(await api("/api/plans/"+entry.id));location.hash="results"}
      catch(error){view.append(note(error.message))}
      finally{open.disabled=false}
    });
    return el("article",[el("h2",entry.district+", "+entry.state),note(entry.season+" · "+value(entry.acres)+" acres"),open],"card");
  });
  view.replaceChildren(el("h1","My Farm Plans"),...rows);
  if(!rows.length)view.append(note("You have no saved plans yet."));
}
async function cropPage(view) {
  const [crops,media]=await Promise.all([api("/api/crops"),credits]);
  view.replaceChildren(el("h1","Crop Information"),...crops.map(crop=>el("article",[
    el("div",[...photo(crop.crop,crop.name,media,true),el("div",[el("h2",crop.name),
      description("Duration",crop.guide.duration),description("Water",crop.guide.water)])],"crop-overview"),
    cropGuide(crop),protection(crop,media)
  ],"card")));
}
function marketPage(view) {
  const pin=el("input");
  Object.assign(pin,{inputMode:"numeric",maxLength:6,pattern:"[1-9][0-9]{5}",required:true,value:plan?.farm.pin||""});
  const district=el("select");
  const choice=el("label",["District",district]);
  choice.hidden=true;
  let resolved="";
  const marketForm=el("form",[el("label",["Indian PIN code",pin]),choice,el("button","Find market prices")],"card stack");
  const results=el("section",[],"card");
  marketForm.addEventListener("submit",async event=>{
    event.preventDefault();
    const button=marketForm.querySelector("button");
    button.disabled=true;
    try{
      const selected=pin.value;
      if(resolved!==selected){
        const districts=(await api("/api/pins/"+selected)).locations;
        district.replaceChildren(...districts.map((p,i)=>new Option(p.district+", "+p.state,i)));
        choice.hidden=districts.length===1;
        resolved=selected;
        if(!choice.hidden){results.replaceChildren(note("Choose the district that serves your farm."));return}
      }
      const rows=await api("/api/market/"+selected+"?location_index="+district.value);
      results.replaceChildren(el("h2","Available quotes"),table(["Crop","Market quote"],rows.map(row=>[row.name,marketText(row.market)])));
    }catch(error){results.replaceChildren(note(error.message))}
    finally{button.disabled=false}
  });
  view.replaceChildren(el("h1","Market Prices"),marketForm,results);
}

async function route() {
  const requested=location.hash.slice(1);
  const pages=["dashboard","plan","results","saved","crops","market"];
  const key=pages.includes(requested) && (requested!=="results" || plan) ? requested : "dashboard";
  for(const page of document.querySelectorAll(".page")) page.hidden=page.id!==key;
  for(const link of document.querySelectorAll(".navigation a")){
    if(link.hash==="#"+(key==="results"?"plan":key))link.setAttribute("aria-current","page");
    else link.removeAttribute("aria-current");
  }
  const view=document.getElementById(key);
  try{
    if(key==="saved")await savedPage(view);
    if(key==="crops")await cropPage(view);
    if(key==="market")marketPage(view);
  }catch(error){view.replaceChildren(note(error.message))}
  if(key==="results")view.querySelector("h1")?.focus();
}
window.addEventListener("hashchange",route);
route();
