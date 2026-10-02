// Export public illustration and recipe fields from a local Pantry Plate checkout.
// Original PNGs stay in the ignored release staging directory, never Git history.
import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(process.argv[2] ?? "../..");
const mobile = resolve(source, "mobile");
const sourceRequire = createRequire(resolve(source, "package.json"));
const mobileRequire = createRequire(resolve(mobile, "package.json"));
const { buildSync } = sourceRequire("esbuild");
const sharp = mobileRequire("sharp");
const json = (file) => JSON.parse(readFileSync(file, "utf8"));
const save = (file, data) =>
  writeFileSync(resolve(root, file), JSON.stringify(data, null, 2) + "\n");
const hash = (data) => createHash("sha256").update(data).digest("hex");
mkdirSync(resolve(root, ".release/originals"), { recursive: true });
buildSync({
  entryPoints: [resolve(mobile, "src/core/data.ts")],
  bundle: true,
  platform: "node",
  format: "cjs",
  outfile: resolve(root, ".release/source-data.cjs"),
});
const { INGREDIENTS, RECIPES } = createRequire(import.meta.url)(
  resolve(root, ".release/source-data.cjs"),
);
const manifests = [
  "manifest.json",
  "additions/manifest.json",
  "imported/manifest.json",
].map((file) => json(resolve(mobile, "assets/ingredients", file)));
const jobs = manifests.flatMap((manifest) => manifest.jobs);
if (
  jobs.length !== 812 ||
  new Set(jobs.map((job) => job.id)).size !== 812 ||
  jobs.some((job) => job.status !== "ready")
)
  throw new Error("Expected 812 completed distinct illustrations.");
if (
  RECIPES.length !== 809 ||
  new Set(RECIPES.map((recipe) => recipe.id)).size !== 809
)
  throw new Error("Expected 809 distinct recipes.");
const catalogById = new Map(INGREDIENTS.map((item) => [item.id, item]));
const prior = json(resolve(root, "metadata/ingredients.json"));
const priorById = new Map(prior.items.map((item) => [item.id, item]));
const grouping = [
  [
    "Meat and poultry",
    /beef|pork|chicken|lamb|veal|turkey|ham|prosciutto|doner|shredded-meat|suet|sausage|kielbasa|pig|frog/,
  ],
  [
    "Fish and shellfish",
    /fish|salmon|shrimp|seafood|barramundi|mackerel|prahok|prawn|crab|tuna|anchov/,
  ],
  ["Dairy and eggs", /cheese|milk|cream|custard|egg-(white|yolk)|bouillon/],
  [
    "Spices and dried seasonings",
    /powder|masala|seasoning|ground-|cajun|ras-el|sazon|jerk|dried-(mint|oregano)|five-spice|annatto|achiote-seeds|harissa-spice|onion-salt|celery-salt|summer-savoury/,
  ],
  [
    "Sauces and condiments",
    /sauce|paste|salsa|dip|aioli|a-oli|stock|broth|jam|jelly|dressing|molasses|cordial|brine|pickle-juice|syrup/,
  ],
  ["Rice and whole grains", /grain|rye$|freekeh|rice$|bulgur|oat/],
  [
    "Pasta noodles and bread",
    /pasta|noodle|bread|pastry|filo|knafeh|wonton|muffin|bun|casabe|arepa/,
  ],
  [
    "Baking sweets and pantry essentials",
    /flour|sugar|chocolate|cookie|biscuit|popcorn|nougat|pudding|meringue|marshmallow|semolina|shortening|crumb|marzipan|delight|cereal|rice-krispies|flax-eggs/,
  ],
  ["Nuts seeds and nut spreads", /seed|nut|pistachio|almond|brittle/],
  ["Berries melons and dried fruit", /berries|currant|sultana|peel|apricot/],
  [
    "Fresh herbs and aromatics",
    /garlic-leaves|mulukhiyah|sorrel|galangal|herb/,
  ],
  [
    "Leafy greens and brassicas",
    /callaloo|morning-glory|vine-leaves|grape-leaves|banana-leaves/,
  ],
  ["Fruiting vegetables", /pepper|squash|tomato/],
  [
    "Mushrooms and specialty vegetables",
    /asparagus|horseradish|palm-heart|vegetable/,
  ],
  ["Tropical fruit", /papaya|tamarind/],
  ["Orchard fruit and citrus", /lemon|orange|zest/],
  [
    "Oils vinegars and preserved foods",
    /oil|vinegar|wine|rum|brandy|beer|cider|marnier|water/,
  ],
];
const items = [];
const prompts = [];
for (const job of jobs) {
  const item = catalogById.get(job.id) ?? catalogById.get(`mealdb-${job.id}`);
  const entry = {
    id: job.id,
    name: job.name,
    group:
      priorById.get(job.id)?.group ??
      grouping.find(([, pattern]) => pattern.test(job.id))?.[0] ??
      "Prepared foods and pantry ingredients",
    category: job.category ?? item?.category ?? "Pantry",
    displayOptimization: job.displayOptimization,
  };
  for (const [extension, artifactName, destination] of [
    ["webp", "display", "images"],
    ["png", "original", ".release/originals"],
  ]) {
    const artifact = job.artifacts[artifactName];
    const origin = resolve(mobile, artifact.path);
    const bytes = readFileSync(origin);
    if (hash(bytes) !== artifact.sha256)
      throw new Error(`Changed source artwork: ${job.id}`);
    const info = await sharp(bytes).metadata();
    if (!info.hasAlpha) throw new Error(`Missing transparency: ${job.id}`);
    const relative = `${destination}/${job.id}.${extension}`;
    copyFileSync(origin, resolve(root, relative));
    entry[extension] = {
      path: extension === "png" ? `originals/${job.id}.png` : relative,
      width: info.width,
      height: info.height,
      bytes: bytes.length,
      sha256: artifact.sha256,
    };
  }
  items.push(entry);
  prompts.push({
    id: job.id,
    prompt: job.prompt,
    method: "OpenAI Codex built-in image generation",
    transparentBackground: true,
    ...(job.subjectClarification
      ? { subjectClarification: job.subjectClarification }
      : {}),
  });
}
const artworkById = new Map(jobs.map((job) => [job.id, job.id]));
for (const alias of manifests[2].aliases)
  artworkById.set(alias.id, alias.artworkId);
const mapping = INGREDIENTS.map((item) => {
  const artworkId = artworkById.get(item.id);
  if (!artworkId) throw new Error(`Unsupported ingredient: ${item.id}`);
  return {
    id: item.id,
    name: item.name,
    unit: item.unit,
    category: item.category,
    artworkId,
  };
});
const mappingById = new Map(mapping.map((item) => [item.id, item]));
const normalize = json(
  resolve(mobile, "assets/recipes/mealdb/normalization.json"),
);
const normalizationById = new Map(normalize.map((item) => [item.id, item]));
const recipes = RECIPES.map((recipe) => {
  const row = (ingredient) => {
    const known = mappingById.get(ingredient.ingredientId);
    if (!known)
      throw new Error(
        `Unmapped recipe ingredient: ${recipe.id}/${ingredient.ingredientId}`,
      );
    return {
      ...ingredient,
      name: ingredient.name ?? known.name,
      artworkId: known.artworkId,
    };
  };
  return {
    id: recipe.id,
    title: recipe.title,
    description: recipe.description,
    minutes: recipe.minutes,
    servings: recipe.servings,
    tags: recipe.tags,
    image: recipe.image,
    ingredients: recipe.ingredients.map(row),
    steps: recipe.steps,
    ...(recipe.sourceUrl ? { sourceUrl: recipe.sourceUrl } : {}),
    ...(recipe.sourceIngredients
      ? { sourceIngredients: recipe.sourceIngredients.map(row) }
      : {}),
    ...(recipe.originalLines ? { originalLines: recipe.originalLines } : {}),
    sourceServings: recipe.sourceServings ?? null,
    ...(recipe.sourceYield ? { sourceYield: recipe.sourceYield } : {}),
    sourceKind: recipe.id.startsWith("mealdb-")
      ? "TheMealDB import"
      : recipe.id.startsWith("asian-")
        ? "Sourced adaptation"
        : "Pantry Plate starter",
    ...(normalizationById.has(recipe.id)
      ? { normalization: normalizationById.get(recipe.id) }
      : {}),
  };
});
save("metadata/ingredients.json", {
  name: "Soft Studio Ingredients",
  version: "1.1.0",
  description:
    "812 AI-generated ingredient illustrations with transparent backgrounds and a uniform white outline",
  count: items.length,
  groups: [...new Set(items.map((item) => item.group))],
  items,
});
save("metadata/prompts.json", prompts);
save("metadata/ingredient-mapping.json", {
  version: "1.1.0",
  count: mapping.length,
  items: mapping,
});
save("metadata/recipes.json", {
  name: "Pantry Plate recipe collection",
  version: "1.1.0",
  count: recipes.length,
  artworkLicense: "CC-BY-4.0",
  recipeRights:
    "Recipe text and referenced photography retain their original source rights; the artwork license does not license third-party recipe content.",
  items: recipes,
});
const columns = [
  "id",
  "name",
  "group",
  "category",
  "webp_path",
  "webp_width",
  "webp_height",
  "webp_bytes",
  "webp_sha256",
  "png_path",
  "png_width",
  "png_height",
  "png_bytes",
  "png_sha256",
];
const csv = (value) => `"${String(value).replaceAll('"', '""')}"`;
writeFileSync(
  resolve(root, "metadata/ingredients.csv"),
  [
    columns.join(","),
    ...items.map((item) =>
      [
        item.id,
        item.name,
        item.group,
        item.category,
        ...["webp", "png"].flatMap((extension) =>
          ["path", "width", "height", "bytes", "sha256"].map(
            (key) => item[extension][key],
          ),
        ),
      ]
        .map(csv)
        .join(","),
    ),
  ].join("\n") + "\n",
);
console.log(
  JSON.stringify({
    illustrations: items.length,
    recipes: recipes.length,
    ingredientMappings: mapping.length,
    webpBytes: items.reduce((sum, item) => sum + item.webp.bytes, 0),
    pngBytes: items.reduce((sum, item) => sum + item.png.bytes, 0),
  }),
);
