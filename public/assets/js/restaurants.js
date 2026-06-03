const list = document.querySelector("#restaurant-list");
const cityFilter = document.querySelector("#city-filter");
const signalFilter = document.querySelector("#signal-filter");
const sourceList = document.querySelector("#source-list");

let restaurants = [];
let sources = [];

function formatDate(value) {
  if (!value) return "Date not listed";
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(date);
}

function renderOptions(select, values) {
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  }
}

function renderFilterOptions(items) {
  const cities = [...new Set(items.map((item) => item.city))].sort();
  const signals = [...new Set(items.map((item) => item.signal))].sort();

  renderOptions(cityFilter, cities);
  renderOptions(signalFilter, signals);
}

function renderStrength(label, value) {
  const max = 5;
  const score = Number(value) || 0;
  const wrapper = document.createElement("div");
  wrapper.className = "score-row";
  wrapper.setAttribute("aria-label", `${label} score ${score} out of ${max}`);

  const text = document.createElement("span");
  text.className = "score-label";
  text.textContent = label;

  const marks = document.createElement("span");
  marks.className = "momentum-score";

  for (let index = 1; index <= max; index += 1) {
    const mark = document.createElement("span");
    mark.className = index <= score ? "is-active" : "";
    marks.append(mark);
  }

  wrapper.append(text, marks);
  return wrapper;
}

function renderScores(item) {
  const scores = item.scores || { momentum: item.signalStrength };
  const wrapper = document.createElement("div");
  wrapper.className = "score-stack";
  wrapper.append(renderStrength("Momentum", scores.momentum || item.signalStrength));

  if (scores.discovery || scores.confidence) {
    wrapper.append(
      renderStrength("Discovery", scores.discovery),
      renderStrength("Confidence", scores.confidence)
    );
  }

  return wrapper;
}

function renderItems() {
  const selectedCity = cityFilter.value;
  const selectedSignal = signalFilter.value;
  const visibleItems = restaurants.filter((item) => {
    const cityMatches = selectedCity === "all" || item.city === selectedCity;
    const signalMatches = selectedSignal === "all" || item.signal === selectedSignal;
    return cityMatches && signalMatches;
  });

  if (visibleItems.length === 0) {
    list.innerHTML = "<p>No restaurant updates match this city yet.</p>";
    return;
  }

  list.replaceChildren(...visibleItems.map((item) => {
    const card = document.createElement("article");
    card.className = "restaurant-card";

    const title = document.createElement("h2");
    title.textContent = item.name;

    const meta = document.createElement("div");
    meta.className = "restaurant-meta";
    meta.innerHTML = `
      <span class="tag">${item.signal}</span>
      <span>${item.city}</span>
      <span>${item.neighborhood}</span>
      <span>${formatDate(item.signalDate)}</span>
    `;

    const summary = document.createElement("p");
    summary.textContent = item.summary;

    const reason = document.createElement("p");
    reason.className = "why-it-matters";
    reason.textContent = item.whyItMatters;

    const strength = renderScores(item);

    const source = document.createElement("a");
    source.className = "source-link";
    source.href = item.sourceUrl;
    source.target = "_blank";
    source.rel = "noopener";
    source.textContent = `Source: ${item.sourceName}`;

    card.append(title, meta, summary, reason, strength, source);
    return card;
  }));
}

function renderSources() {
  sourceList.replaceChildren(...sources.map((source) => {
    const card = document.createElement("article");
    card.className = "source-card";

    const title = document.createElement("h3");
    title.textContent = source.name;

    const city = document.createElement("p");
    city.className = "source-city";
    city.textContent = source.city;

    const use = document.createElement("p");
    use.textContent = source.use;

    const link = document.createElement("a");
    link.href = source.url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = "Open source";

    card.append(city, title, use, link);
    return card;
  }));
}

async function loadRestaurants() {
  try {
    const response = await fetch("data/restaurants.json");
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);

    const data = await response.json();
    restaurants = data.items;
    sources = data.sources;
    restaurants.sort((a, b) => {
      const signalCompare = Number(b.signalStrength) - Number(a.signalStrength);
      if (signalCompare !== 0) return signalCompare;
      return (b.signalDate || "").localeCompare(a.signalDate || "");
    });

    renderFilterOptions(restaurants);
    renderItems();
    renderSources();
  } catch (error) {
    list.innerHTML = "<p>Restaurant updates could not be loaded.</p>";
    console.error(error);
  }
}

cityFilter.addEventListener("change", renderItems);
signalFilter.addEventListener("change", renderItems);
loadRestaurants();
