import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const json = (file) => JSON.parse(readFileSync(resolve(root, file), "utf8"));
const config = json("dataset.json");
const catalog = json("metadata/ingredients.json");
const prompts = json("metadata/prompts.json");
const mapping = json("metadata/ingredient-mapping.json");
const recipes = json("metadata/recipes.json");
const unique = (items) => new Set(items.map((item) => item.id)).size;
if (
  config.ingredientCount !== 812 ||
  catalog.count !== config.ingredientCount ||
  catalog.items.length !== catalog.count ||
  unique(catalog.items) !== catalog.count
)
  throw new Error("Ingredient count/IDs do not match.");
if (prompts.length !== catalog.count || unique(prompts) !== catalog.count)
  throw new Error("Prompt count/IDs do not match.");
if (
  new Set(catalog.items.map((item) => item.group)).size !==
  catalog.groups.length
)
  throw new Error("Group count does not match.");
if (
  readdirSync(resolve(root, "images")).filter((name) => name.endsWith(".webp"))
    .length !== catalog.count
)
  throw new Error("Display file count does not match.");
const artworkIds = new Set(catalog.items.map((item) => item.id));
for (const item of catalog.items) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(item.id))
    throw new Error(`Invalid ID: ${item.id}`);
  const bytes = readFileSync(resolve(root, item.webp.path));
  if (
    bytes.length !== item.webp.bytes ||
    createHash("sha256").update(bytes).digest("hex") !== item.webp.sha256
  )
    throw new Error(`Invalid artwork: ${item.id}`);
  if (
    bytes.toString("ascii", 0, 4) !== "RIFF" ||
    bytes.toString("ascii", 8, 12) !== "WEBP"
  )
    throw new Error(`Not WebP: ${item.id}`);
  if (
    item.webp.width !== 320 ||
    item.webp.height !== 320 ||
    item.displayOptimization?.version !== "normalized-v1" ||
    item.displayOptimization?.whiteOutlinePixels !== 6 ||
    item.displayOptimization?.subjectPixels !== 284
  )
    throw new Error(`Inconsistent display outline/scale: ${item.id}`);
  if (
    !prompts.some(
      (prompt) =>
        prompt.id === item.id && prompt.transparentBackground && prompt.prompt,
    )
  )
    throw new Error(`Missing prompt: ${item.id}`);
}
if (
  mapping.count !== mapping.items.length ||
  unique(mapping.items) !== mapping.count ||
  mapping.items.some((item) => !artworkIds.has(item.artworkId))
)
  throw new Error("Incomplete ingredient mapping.");
const mapped = new Map(mapping.items.map((item) => [item.id, item.artworkId]));
if (mapped.get("mealdb-rice-flour-pancakes") !== "rice-paper")
  throw new Error("Vietnamese wrappers must use rice paper artwork.");
if (
  config.recipeCount !== 809 ||
  recipes.count !== config.recipeCount ||
  recipes.items.length !== recipes.count ||
  unique(recipes.items) !== recipes.count
)
  throw new Error("Recipe count/IDs do not match.");
for (const recipe of recipes.items) {
  if (
    !recipe.title ||
    !recipe.steps?.length ||
    recipe.steps.some((step) => typeof step !== "string" || !step.trim()) ||
    !recipe.ingredients?.length
  )
    throw new Error(`Incomplete recipe: ${recipe.id}`);
  if (
    !Number.isFinite(recipe.servings) ||
    recipe.servings <= 0 ||
    !Number.isFinite(recipe.minutes) ||
    recipe.minutes <= 0
  )
    throw new Error(`Invalid recipe reference batch: ${recipe.id}`);
  for (const row of [
    ...recipe.ingredients,
    ...(recipe.sourceIngredients ?? []),
  ]) {
    if (
      !row.name ||
      mapped.get(row.ingredientId) !== row.artworkId ||
      !artworkIds.has(row.artworkId)
    )
      throw new Error(
        `Unillustrated recipe ingredient: ${recipe.id}/${row.ingredientId}`,
      );
  }
  for (const row of recipe.ingredients)
    if (
      !Number.isFinite(row.quantity) ||
      row.quantity <= 0 ||
      !["g", "ml", "each"].includes(row.unit)
    )
      throw new Error(`Invalid planning quantity: ${recipe.id}`);
  if (
    recipe.sourceKind !== "Pantry Plate starter" &&
    !/^https?:\/\//.test(recipe.sourceUrl ?? "")
  )
    throw new Error(`Missing source attribution: ${recipe.id}`);
}
for (const file of [
  "metadata/ingredients.json",
  "metadata/prompts.json",
  "metadata/ingredients.csv",
  "metadata/ingredient-mapping.json",
  "metadata/recipes.json",
]) {
  const text = readFileSync(resolve(root, file), "utf8");
  if (
    /(?:[A-Za-z]:[\\/]+Users|codex-overlays|originalToolPath|access_token|api_key)/i.test(
      text,
    )
  )
    throw new Error(`Private provenance leaked into ${file}`);
}
if (process.argv.includes("--release")) {
  if (config.license !== "CC-BY-4.0")
    throw new Error("The image license must match the published collection.");
  for (const file of [
    "LICENSE",
    "ATTRIBUTION.md",
    "DATASET_CARD.md",
    "README.md",
    "RECIPE_SOURCES.md",
  ])
    if (!readFileSync(resolve(root, file), "utf8").trim())
      throw new Error(`Missing release document: ${file}`);
}
console.log(
  `Verified ${catalog.count} illustrations, ${catalog.groups.length} groups, ${mapping.count} ingredient mappings, ${recipes.count} complete recipes, hashes, uniform outlines and public metadata.`,
);
