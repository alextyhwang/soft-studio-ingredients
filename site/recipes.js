const $ = (selector) => document.querySelector(selector);
const normalize = (value) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
const pageSize = 48;
let recipes = [];
let images = new Map();
let filtered = [];
let limit = pageSize;
let loaded = false;
let loading = false;
const dialog = $("#recipe-detail");
const element = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
function icon(row, size = 48) {
  const image = element("img");
  image.src = images.get(row.artworkId);
  image.alt = "";
  image.width = image.height = size;
  image.loading = "lazy";
  image.decoding = "async";
  return image;
}
function showRecipe(recipe) {
  $("#recipe-detail-title").textContent = recipe.title;
  $("#recipe-detail-meta").textContent =
    `${recipe.minutes} min · ${recipe.servings} reference servings`;
  $("#recipe-description").textContent = recipe.description;
  const rows = recipe.sourceIngredients?.length
    ? recipe.sourceIngredients
    : recipe.ingredients;
  $("#recipe-ingredients").replaceChildren(
    ...rows.map((row) => {
      const item = element("li");
      item.append(
        icon(row),
        element("span", "", row.name),
        element(
          "span",
          "recipe-measure",
          row.measure ?? `${row.quantity} ${row.unit}`,
        ),
      );
      return item;
    }),
  );
  $("#recipe-steps").replaceChildren(
    ...recipe.steps.map((step) => element("li", "", step)),
  );
  const source = $("#recipe-source");
  const url = recipe.normalization?.publisherUrl || recipe.sourceUrl;
  source.hidden = !url;
  if (url) source.href = url;
  $("#recipe-source-note").textContent =
    recipe.sourceKind === "Pantry Plate starter"
      ? "A Pantry Plate starter recipe."
      : "Source measures are shown where available. Planning quantities, time and reference servings may be approximate. Recipe text retains its source rights.";
  history.replaceState(null, "", `#recipe=${encodeURIComponent(recipe.id)}`);
  if (!dialog.open) dialog.showModal();
}
$("#recipe-close").addEventListener("click", () => dialog.close());
dialog.addEventListener("close", () => {
  if (location.hash.startsWith("#recipe="))
    history.replaceState(null, "", "#recipes");
});
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
function render() {
  const words = normalize($("#recipe-search").value.trim())
    .split(/\s+/)
    .filter(Boolean);
  const tag = $("#recipe-tag").value;
  filtered = recipes.filter(
    (recipe) =>
      (!tag || recipe.tags.includes(tag)) &&
      words.every((word) =>
        normalize(
          `${recipe.title} ${recipe.tags.join(" ")} ${recipe.ingredients.map((row) => row.name).join(" ")} ${(recipe.sourceIngredients ?? []).map((row) => row.name).join(" ")}`,
        ).includes(word),
      ),
  );
  $("#recipe-count").textContent =
    `${filtered.length} of ${recipes.length} recipes`;
  $("#recipe-empty").hidden = filtered.length !== 0;
  $("#recipe-more").hidden = filtered.length <= limit;
  $("#recipe-gallery").replaceChildren(
    ...filtered.slice(0, limit).map((recipe) => {
      const button = element("button", "recipe-card");
      button.type = "button";
      button.setAttribute("aria-label", `View recipe: ${recipe.title}`);
      const art = element("div", "recipe-card-art");
      const rows = recipe.sourceIngredients?.length
        ? recipe.sourceIngredients
        : recipe.ingredients;
      const distinct = [
        ...new Map(rows.map((row) => [row.artworkId, row])).values(),
      ].slice(0, 4);
      art.append(...distinct.map((row) => icon(row, 80)));
      button.append(
        art,
        element("span", "recipe-card-title", recipe.title),
        element(
          "span",
          "recipe-card-meta",
          `${recipe.minutes} min · ${recipe.tags.slice(0, 2).join(" · ")}`,
        ),
      );
      button.addEventListener("click", () => showRecipe(recipe));
      return button;
    }),
  );
}
for (const [id, event] of [
  ["recipe-search", "input"],
  ["recipe-tag", "change"],
]) {
  $(`#${id}`).addEventListener(event, () => {
    limit = pageSize;
    render();
  });
}
$("#recipe-reset").addEventListener("click", () => {
  $("#recipe-search").value = "";
  $("#recipe-tag").value = "";
  limit = pageSize;
  render();
  $("#recipe-search").focus();
});
$("#recipe-more").addEventListener("click", () => {
  const prior = Math.min(limit, filtered.length);
  limit += pageSize;
  render();
  $("#recipe-gallery").children[prior]?.focus({ preventScroll: true });
});
async function loadRecipes() {
  if (loaded || loading) return;
  loading = true;
  $("#recipe-error").hidden = true;
  $("#recipe-count").textContent = "Loading recipes…";
  try {
    const [recipeResponse, imageResponse] = await Promise.all([
      fetch("metadata/recipes.json"),
      fetch("ingredients.json"),
    ]);
    if (!recipeResponse.ok || !imageResponse.ok)
      throw new Error("Recipes unavailable");
    const catalog = await recipeResponse.json();
    const artwork = await imageResponse.json();
    recipes = catalog.items;
    images = new Map(artwork.map((item) => [item.id, item.image]));
    if (
      !recipes.length ||
      recipes.length !== catalog.count ||
      new Set(recipes.map((recipe) => recipe.id)).size !== recipes.length ||
      recipes.some((recipe) =>
        [...recipe.ingredients, ...(recipe.sourceIngredients ?? [])].some(
          (row) => !images.has(row.artworkId),
        ),
      )
    )
      throw new Error("Incomplete recipe collection");
    $("#recipe-tag").replaceChildren(new Option("All cuisines and tags", ""));
    [...new Set(recipes.flatMap((recipe) => recipe.tags))]
      .sort((a, b) => a.localeCompare(b))
      .forEach((tag) => $("#recipe-tag").add(new Option(tag, tag)));
    loaded = true;
    render();
    if (location.hash.startsWith("#recipe=")) {
      const recipe = recipes.find(
        (item) => item.id === decodeURIComponent(location.hash.slice(8)),
      );
      if (recipe) showRecipe(recipe);
    }
  } catch {
    $("#recipe-count").textContent = "Recipes unavailable";
    $("#recipe-error").hidden = false;
  } finally {
    loading = false;
  }
}
$("#recipe-retry").addEventListener("click", loadRecipes);
window.addEventListener("hashchange", () => {
  if (location.hash.startsWith("#recipe=")) {
    if (!loaded) void loadRecipes();
    else {
      const recipe = recipes.find(
        (item) => item.id === decodeURIComponent(location.hash.slice(8)),
      );
      if (recipe) showRecipe(recipe);
    }
  }
});
if (location.hash.startsWith("#recipe=")) void loadRecipes();
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        observer.disconnect();
        void loadRecipes();
      }
    },
    { rootMargin: "400px" },
  );
  observer.observe($("#recipes"));
} else void loadRecipes();
