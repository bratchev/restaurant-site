const list = document.querySelector("#restaurant-list");
const cityFilter = document.querySelector("#city-filter");

let restaurants = [];

function formatDate(value) {
  if (!value) return "Date not listed";
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(date);
}

function renderCityOptions(items) {
  const cities = [...new Set(items.map((item) => item.city))].sort();

  for (const city of cities) {
    const option = document.createElement("option");
    option.value = city;
    option.textContent = city;
    cityFilter.append(option);
  }
}

function renderItems() {
  const selectedCity = cityFilter.value;
  const visibleItems = selectedCity === "all"
    ? restaurants
    : restaurants.filter((item) => item.city === selectedCity);

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
      <span class="tag">${item.status}</span>
      <span>${item.city}</span>
      <span>${formatDate(item.expectedDate)}</span>
    `;

    const summary = document.createElement("p");
    summary.textContent = item.summary;

    const source = document.createElement("a");
    source.className = "source-link";
    source.href = item.sourceUrl;
    source.target = "_blank";
    source.rel = "noopener";
    source.textContent = `Source: ${item.sourceName}`;

    card.append(title, meta, summary, source);
    return card;
  }));
}

async function loadRestaurants() {
  try {
    const response = await fetch("data/restaurants.json");
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);

    restaurants = await response.json();
    restaurants.sort((a, b) => {
      const cityCompare = a.city.localeCompare(b.city);
      if (cityCompare !== 0) return cityCompare;
      return (b.publishedDate || "").localeCompare(a.publishedDate || "");
    });

    renderCityOptions(restaurants);
    renderItems();
  } catch (error) {
    list.innerHTML = "<p>Restaurant updates could not be loaded.</p>";
    console.error(error);
  }
}

cityFilter.addEventListener("change", renderItems);
loadRestaurants();
