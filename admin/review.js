const list = document.querySelector("#candidate-list");
const cityFilter = document.querySelector("#city-filter");
const statusFilter = document.querySelector("#status-filter");
const downloadButton = document.querySelector("#download-approved");

let candidates = [];

function valueFor(candidate, path) {
  return path.split(".").reduce((value, key) => value?.[key], candidate) ?? "";
}

function setValue(candidate, path, value) {
  const parts = path.split(".");
  let target = candidate;
  for (const part of parts.slice(0, -1)) {
    target[part] = target[part] || {};
    target = target[part];
  }
  target[parts.at(-1)] = value;
}

function field(candidate, path, label, type = "text") {
  const wrapper = document.createElement("label");
  wrapper.textContent = label;

  const input = type === "textarea" ? document.createElement("textarea") : document.createElement("input");
  input.value = valueFor(candidate, path);
  input.addEventListener("input", () => setValue(candidate, path, input.value));

  wrapper.append(input);
  return wrapper;
}

function score(candidate, key, label) {
  const wrapper = document.createElement("label");
  const title = document.createElement("span");
  const input = document.createElement("input");
  const value = document.createElement("strong");

  title.textContent = label;
  input.type = "range";
  input.min = "1";
  input.max = "5";
  input.value = candidate.event[key] || 3;
  value.textContent = input.value;

  input.addEventListener("input", () => {
    candidate.event[key] = Number(input.value);
    value.textContent = input.value;
  });

  wrapper.append(title, input, value);
  return wrapper;
}

function renderCityOptions() {
  const cities = [...new Set(candidates.map((candidate) => candidate.city))].sort();
  for (const city of cities) {
    const option = document.createElement("option");
    option.value = city;
    option.textContent = city;
    cityFilter.append(option);
  }
}

function render() {
  const selectedCity = cityFilter.value;
  const selectedStatus = statusFilter.value;
  const visible = candidates.filter((candidate) => {
    const cityMatches = selectedCity === "all" || candidate.city === selectedCity;
    const statusMatches = selectedStatus === "all" || candidate.status === selectedStatus;
    return cityMatches && statusMatches;
  });

  if (visible.length === 0) {
    list.innerHTML = "<p>No candidates match the current filters.</p>";
    return;
  }

  list.replaceChildren(...visible.map((candidate) => {
    const card = document.createElement("article");
    card.className = "candidate-card";
    card.dataset.status = candidate.status;

    const fields = document.createElement("div");
    fields.className = "candidate-fields";
    fields.append(
      field(candidate, "name", "Restaurant"),
      field(candidate, "city", "City"),
      field(candidate, "neighborhood", "Neighborhood"),
      field(candidate, "event.type", "Event type"),
      field(candidate, "summary", "Summary", "textarea"),
      field(candidate, "whyItMatters", "Why it matters", "textarea")
    );
    fields.querySelectorAll("label:nth-last-child(-n+2)").forEach((label) => label.classList.add("wide"));

    const side = document.createElement("aside");
    side.className = "candidate-side";

    const source = document.createElement("a");
    source.className = "source-link";
    source.href = candidate.event.url;
    source.target = "_blank";
    source.rel = "noopener";
    source.textContent = `${candidate.event.sourceName}: ${candidate.event.url}`;

    const scores = document.createElement("div");
    scores.className = "score-grid";
    scores.append(
      score(candidate, "momentum", "Momentum"),
      score(candidate, "discovery", "Discovery"),
      score(candidate, "confidence", "Confidence")
    );

    const actions = document.createElement("div");
    actions.className = "actions";
    for (const [status, label] of [["approved", "Approve"], ["rejected", "Reject"], ["pending", "Pending"]]) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.action = status === "pending" ? "pending" : status.replace("ed", "e");
      button.textContent = label;
      button.addEventListener("click", () => {
        candidate.status = status;
        render();
      });
      actions.append(button);
    }

    side.append(source, scores, actions);
    card.append(fields, side);
    return card;
  }));
}

function downloadApproved() {
  const approved = {
    generatedAt: new Date().toISOString(),
    candidates: candidates.filter((candidate) => candidate.status === "approved")
  };
  const blob = new Blob([JSON.stringify(approved, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "approved-candidates.json";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function load() {
  const response = await fetch("../data-work/candidates.json");
  if (!response.ok) {
    list.innerHTML = "<p>Run the scanner first: python3 tools/scan_restaurant_sources.py --weeks 12</p>";
    return;
  }

  const data = await response.json();
  candidates = data.candidates;
  renderCityOptions();
  render();
}

cityFilter.addEventListener("change", render);
statusFilter.addEventListener("change", render);
downloadButton.addEventListener("click", downloadApproved);
load();
