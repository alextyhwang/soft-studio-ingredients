import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const config = JSON.parse(readFileSync(resolve(root, "dataset.json"), "utf8"));
const catalog = JSON.parse(
  readFileSync(resolve(root, "metadata/ingredients.json"), "utf8"),
);
const prompts = JSON.parse(
  readFileSync(resolve(root, "metadata/prompts.json"), "utf8"),
);
if (
  catalog.count !== 520 ||
  catalog.items.length !== 520 ||
  new Set(catalog.items.map((i) => i.id)).size !== 520
)
  throw new Error("Ingredient count/IDs do not match.");
if (prompts.length !== 520 || new Set(prompts.map((i) => i.id)).size !== 520)
  throw new Error("Prompt count/IDs do not match.");
if (new Set(catalog.items.map((i) => i.group)).size !== 20)
  throw new Error("Expected 20 categories.");
if (
  readdirSync(resolve(root, "images")).filter((name) => name.endsWith(".webp"))
    .length !== 520
)
  throw new Error("Expected exactly 520 display files.");
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
  if (item.webp.width > 320 || item.webp.height > 320)
    throw new Error(`Display too large: ${item.id}`);
  if (
    !prompts.some(
      (prompt) =>
        prompt.id === item.id && prompt.transparentBackground && prompt.prompt,
    )
  )
    throw new Error(`Missing prompt: ${item.id}`);
}
for (const file of [
  "metadata/ingredients.json",
  "metadata/prompts.json",
  "metadata/ingredients.csv",
]) {
  const text = readFileSync(resolve(root, file), "utf8");
  if (
    /(?:[A-Za-z]:\\\\?Users|codex-overlays|originalToolPath|access_token|api_key)/i.test(
      text,
    )
  )
    throw new Error(`Private provenance leaked into ${file}`);
}
if (process.argv.includes("--release")) {
  if (!["CC-BY-4.0", "CC0-1.0"].includes(config.license))
    throw new Error("Choose the image license before publishing.");
  for (const file of [
    "LICENSE",
    "ATTRIBUTION.md",
    "DATASET_CARD.md",
    "README.md",
  ]) {
    if (!readFileSync(resolve(root, file), "utf8").trim())
      throw new Error(`Missing release document: ${file}`);
  }
}
console.log(
  `Verified 520 distinct display images, 20 groups, hashes, sizes, metadata and prompts${process.argv.includes("--release") ? ", and release license" : ""}.`,
);
