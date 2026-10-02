const $ = (selector) => document.querySelector(selector);
const search = $("#search");
const group = $("#group");
const gallery = $("#gallery");
const dialog = $("#detail");
let ingredients = [];
let visible = [];
let current = 0;
let showcase = 0;
const showcases = [
  ["cucumber", "tomato", "cheese", "avocado"],
  ["strawberry", "milk", "honey", "bread"],
  ["bok-choy", "shiitake", "tofu", "soy"],
  ["lemon", "red-cabbage", "cherry", "basil"],
];
const normalize = (value) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

function setBackdrop(surface) {
  document.documentElement.dataset.backdrop = surface;
  document.querySelectorAll("[data-surface]").forEach((button) => {
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.surface === surface),
    );
  });
  try {
    localStorage.setItem("ingredient-gallery-backdrop", surface);
  } catch {
    /* Browsing still works without storage. */
  }
}
document
  .querySelectorAll("[data-surface]")
  .forEach((button) =>
    button.addEventListener("click", () => setBackdrop(button.dataset.surface)),
  );
try {
  const saved = localStorage.getItem("ingredient-gallery-backdrop");
  if (["light", "dark", "check"].includes(saved)) setBackdrop(saved);
} catch {
  /* Keep the default backdrop. */
}

function showDetail(index) {
  current = (index + visible.length) % visible.length;
  const item = visible[current];
  $("#detail-title").textContent = item.name;
  $("#detail-group").textContent = item.group;
  $("#detail-image").src = item.image;
  $("#detail-image").alt = item.name;
  $("#detail-position").textContent = `${current + 1} / ${visible.length}`;
  $("#download").href = item.image;
  $("#download").download = `${item.id}.webp`;
  if (!dialog.open) dialog.showModal();
}
$(".close").addEventListener("click", () => dialog.close());
$("#previous").addEventListener("click", () => showDetail(current - 1));
$("#next").addEventListener("click", () => showDetail(current + 1));
dialog.addEventListener("click", (event) => {
  if (event.target !== dialog) return;
  const box = dialog.getBoundingClientRect();
  if (
    event.clientX < box.left ||
    event.clientX > box.right ||
    event.clientY < box.top ||
    event.clientY > box.bottom
  )
    dialog.close();
});
dialog.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    event.preventDefault();
    showDetail(current + (event.key === "ArrowRight" ? 1 : -1));
  }
});

function render() {
  const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
  visible = ingredients.filter(
    (item) =>
      (!group.value || item.group === group.value) &&
      words.every((word) =>
        normalize(`${item.name} ${item.id}`).includes(word),
      ),
  );
  $("#result-count").textContent =
    `${visible.length} of ${ingredients.length} ingredients`;
  $("#empty").hidden = visible.length !== 0;
  const fragment = document.createDocumentFragment();
  const groups = new Map();
  visible.forEach((item, index) => {
    if (!groups.has(item.group)) {
      const section = document.createElement("section");
      section.className = "ingredient-group";
      const heading = document.createElement("div");
      heading.className = "group-heading";
      const title = document.createElement("h2");
      title.textContent = item.group;
      const count = document.createElement("span");
      const grid = document.createElement("div");
      grid.className = "grid";
      heading.append(title, count);
      section.append(heading, grid);
      fragment.append(section);
      groups.set(item.group, { grid, count, total: 0 });
    }
    const section = groups.get(item.group);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "card";
    button.setAttribute("aria-label", `View ${item.name}`);
    const image = document.createElement("img");
    image.src = item.image;
    image.alt = "";
    image.width = 320;
    image.height = 320;
    image.loading = "lazy";
    image.decoding = "async";
    const name = document.createElement("span");
    name.className = "card-name";
    name.textContent = item.name;
    const hint = document.createElement("span");
    hint.className = "card-hint";
    hint.textContent = "↗";
    hint.setAttribute("aria-hidden", "true");
    button.append(image, name, hint);
    button.addEventListener("click", () => showDetail(index));
    section.grid.append(button);
    section.count.textContent = String(++section.total);
  });
  gallery.replaceChildren(fragment);
}

search.addEventListener("input", render);
group.addEventListener("change", render);
$("#reset").addEventListener("click", () => {
  search.value = "";
  group.value = "";
  render();
  search.focus();
});

function renderShowcase(announce = false) {
  const hero = $("#hero-art");
  const items = showcases[showcase].map((id) =>
    ingredients.find((item) => item.id === id),
  );
  hero.replaceChildren(
    ...items.map((item) => {
      const image = document.createElement("img");
      image.src = item.image;
      image.alt = "";
      image.width = 320;
      image.height = 320;
      image.decoding = "async";
      return image;
    }),
  );
  if (announce)
    $("#hero-status").textContent =
      `Showing ${items.map((item) => item.name).join(", ")}.`;
}

$("#shuffle-hero").addEventListener("click", () => {
  if (!ingredients.length) return;
  showcase = (showcase + 1) % showcases.length;
  renderShowcase(true);
});

async function load() {
  $("#error").hidden = true;
  $("#result-count").textContent = "Loading the collection…";
  try {
    const response = await fetch("ingredients.json");
    if (!response.ok) throw new Error("Collection unavailable");
    ingredients = await response.json();
    if (
      !ingredients.length ||
      new Set(ingredients.map((item) => item.id)).size !== ingredients.length
    )
      throw new Error("Incomplete collection");
    group.replaceChildren(new Option("All categories", ""));
    [...new Set(ingredients.map((item) => item.group))].forEach((name) =>
      group.add(new Option(name, name)),
    );
    renderShowcase();
    render();
  } catch {
    $("#result-count").textContent = "Collection unavailable";
    $("#error").hidden = false;
  }
}
$("#retry").addEventListener("click", load);
load();

$("#copy-credit").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText($("#credit-text").textContent);
    $("#credit-status").textContent = "Credit copied.";
  } catch {
    $("#credit-status").textContent = "Select and copy the credit line above.";
  }
});
