# Soft Studio Ingredients

**812 transparent ingredient illustrations and 809 recipes for apps, menus, and meal planners.**

[Browse the collection](https://soft-studio-ingredients.vercel.app) · [Browse recipes](https://soft-studio-ingredients.vercel.app/#recipes) · [Download v1.1.0](https://github.com/alextyhwang/soft-studio-ingredients/releases/tag/v1.1.0) · [Artwork license](LICENSE)

|                                   |                             |                                             |                                         |
| --------------------------------- | --------------------------- | ------------------------------------------- | --------------------------------------- |
| ![Bok choy](images/bok-choy.webp) | ![Lemon](images/lemon.webp) | ![Shiitake mushrooms](images/shiitake.webp) | ![Red cabbage](images/red-cabbage.webp) |

Version 1.1.0 adds **292 illustrations**: 39 recipe ingredients and 253 subjects from the expanded cookbook. All 812 display files now share transparent 320 × 320 canvases, a consistent Soft Studio food style, and a uniform six-pixel white outline. Stable ingredient IDs are retained.

The landing page includes ingredient search, 21 category filters, light/dark/checkerboard previews, individual image downloads, and a searchable recipe browser with ingredient illustrations, source measures, cooking steps and source links.

## Downloads

- [WebP pack](https://github.com/alextyhwang/soft-studio-ingredients/releases/download/v1.1.0/soft-studio-ingredients-webp-v1.1.0.zip): all 812 optimized illustrations. Image files total 12.86 MB.
- [Original PNG pack](https://github.com/alextyhwang/soft-studio-ingredients/releases/download/v1.1.0/soft-studio-ingredients-png-v1.1.0.zip): all 812 generated originals. Image files total 1.19 GB.
- [Recipe + artwork pack](https://github.com/alextyhwang/soft-studio-ingredients/releases/download/v1.1.0/soft-studio-recipes-v1.1.0.zip): all 809 recipes, 1,192 ingredient mappings, and all 812 WebP illustrations.
- [JSON recipe collection](metadata/recipes.json), [ingredient mappings](metadata/ingredient-mapping.json), [CSV artwork metadata](metadata/ingredients.csv), [JSON artwork metadata](metadata/ingredients.json), and [recorded prompts](metadata/prompts.json).
- [Release checksums](https://github.com/alextyhwang/soft-studio-ingredients/releases/download/v1.1.0/SHA256SUMS.txt): verify the downloaded archives and metadata files.

Image packs include metadata, the dataset card and attribution documents. Original PNGs are release downloads; optimized images are included in Git history.

## Use an image

```html
<img src="/images/bok-choy.webp" alt="Bok choy" width="160" height="160" />
```

Load `metadata/ingredients.json` for stable artwork IDs, paths, sizes and SHA-256 hashes. Recipe ingredient identities are separate from decorative artwork: `metadata/ingredient-mapping.json` maps 1,192 catalog IDs to 812 illustrations. Every normalized and original-source ingredient row in every recipe includes its `artworkId`.

```js
const { items: recipes } = await fetch("/metadata/recipes.json").then((r) =>
  r.json(),
);
const row = recipes[0].ingredients[0];
console.log(row.name, row.artworkId); // Keep the ingredient name; use the matching illustration.
```

## Artwork license and recipe sources

The **illustrations** are licensed under **CC BY 4.0**. Use and adapt them, including commercially, with credit, a license link and a notice of changes. Suggested credit:

> Soft Studio Ingredients by Alex Wang, licensed under CC BY 4.0.

See [ATTRIBUTION.md](ATTRIBUTION.md) and [LICENSE](LICENSE). Recipe text and referenced photography retain their original source rights; the illustration license does not license third-party recipe content. Publisher/API links and source measures are preserved. See [RECIPE_SOURCES.md](RECIPE_SOURCES.md).

## Provenance

The images were AI-generated with built-in image generation, then checked with automated file validation and assistant visual review. The 253 newest subjects include 75 final composition/form refinements, reviewed on light and dark backgrounds. Original PNGs can have different rims and margins from normalized display WebPs. These are illustrations, not photographic identification ground truth. See [DATASET_CARD.md](DATASET_CARD.md).

## Build and verify

Node.js 20 or newer is sufficient for the static build; no dependencies are required.

```sh
npm run verify
npm run check
npm run build
python -m http.server 8094 --directory dist
```

The verifier checks all 812 image hashes and display policies, 1,192 ingredient mappings, and every source/normalized ingredient row in all 809 recipes. The build emits a standalone static site in `dist/`.

Optional browser checks require Python Playwright with Chromium and WebKit:

```sh
python scripts/check-site.py http://localhost:8094
```

The checks cover all image URLs/hashes, recipe search and tag filters, pagination, ingredient/details dialogs, deep links, source credits, keyboard dismissal and layouts at 320, 390, 768 and 1440 pixels. Browser emulation does not establish physical-device touch behavior.

To rebuild exports from a local Pantry Plate checkout with its dependencies installed:

```sh
node scripts/import-pantry-plate.mjs /path/to/jimmyxalexfoods
python scripts/package-release.py
```

The exporter copies PNG originals into ignored `.release/originals/`. The packager verifies image hashes and ZIP contents, then writes release assets and checksums under `.release/artifacts/`. Local machine paths and account data are excluded from public metadata.
