# Soft Studio Ingredients

Version: 1.1.0. Publisher: Alex Wang. Illustration license: CC BY 4.0.

## Contents

812 distinct ingredient illustrations across 21 culinary groups, plus 809 recipes and 1,192 ingredient-to-artwork mappings. This release adds 292 illustrations to version 1.0.0. The original release remains available under its versioned tag and downloads.

| Resource                            | Contents                                                                                                    |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `images/`                           | 812 transparent, normalized 320 × 320 WebP files                                                            |
| Original PNG release archive        | 812 full-resolution generated PNGs; dimensions vary                                                         |
| `metadata/ingredients.json` and CSV | IDs, names, groups, categories, dimensions, bytes, hashes and display policy                                |
| `metadata/prompts.json`             | Recorded final generation/correction prompts                                                                |
| `metadata/ingredient-mapping.json`  | 1,192 recipe/catalog identities mapped to decorative artwork IDs                                            |
| `metadata/recipes.json`             | 809 recipes with normalized planning quantities, source measures, steps, tags, source links and artwork IDs |
| `RECIPE_SOURCES.md`                 | Recipe attribution and scope of rights                                                                      |

Display WebPs total 12,859,816 bytes. Original PNGs total 1,193,753,568 bytes. ZIP sizes include metadata and documents. Originals are distributed through GitHub Releases rather than Git history.

## Creation and processing

The illustrations were generated individually using built-in OpenAI image generation with transparent backgrounds. Their shared direction uses diffuse upper-left studio light, realistic food materials and a compact readable silhouette. No specific underlying image model/version is claimed.

All display derivatives use the same normalized-v1 policy: 320-pixel square canvas, a maximum 284-pixel subject and a deterministic six-pixel white outline. Original PNGs were not changed by normalization, so their rims and margins may differ. Version 1.1.0 also updates the original 520 WebP derivatives to this uniform policy while retaining their IDs.

The newest 253 subjects were visually reviewed on light and dark backgrounds at 64 pixels. Seventy-five form/composition refinements removed clutter or corrected ingredient interpretation, including raw knafeh pastry, water spinach and shredded cooked codfish bulljaw. Earlier 39 additions use the same artwork pipeline. Automated checks verify hashes, dimensions, transparency during export, unique IDs, prompts and complete recipe-to-artwork coverage.

Recorded prompts describe the final generation or corrective edit; they do not promise pixel-identical regeneration. Only public dataset fields are exported. Local machine paths, credentials and account data are excluded.

## Recipe data

The collection contains 14 Pantry Plate starter recipes, 25 sourced Asian adaptations and 770 additional TheMealDB imports. Original source names and measures remain separate from normalized planning quantities. Artwork aliases preserve recipe ingredient identities rather than substituting ingredients.

Imported recipe yield/time and some quantities are estimates; original measures and source links remain available for cooking. Recipe photos are referenced by their original URLs and are not bundled in these archives. The landing-page recipe cards use ingredient illustrations.

## Intended uses and limits

Use these synthetic illustrations in recipe interfaces, pantry apps, menus, educational material and design prototypes. They are not photographs, nutritional measurements or scientific identification ground truth. Similar cultivars, powders, oils and preparations may look alike. Category labels are catalog groupings, not storage guidance.

No train/validation/test split is supplied. This is an illustration collection, not a benchmark.

## Rights and attribution

The illustrations are available under CC BY 4.0 with credit, a license link and modification notices. See [ATTRIBUTION.md](ATTRIBUTION.md) and [LICENSE](LICENSE). The license applies to rights held by the publisher.

Recipe text and referenced photography retain their original source rights; the artwork license does not grant rights to third-party recipe content. See [RECIPE_SOURCES.md](RECIPE_SOURCES.md), and each recipe's publisher/API/source URLs.

## Versioning and corrections

Pin exact assets using SHA-256 hashes and the `v1.1.0` tag. Existing illustration IDs remain stable. Report issues with the ingredient/recipe ID and release version. Corrections should ship in a new release rather than silently replace earlier release downloads.
