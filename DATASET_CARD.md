# Soft Studio Ingredients

Version: 1.0.0. Publisher: Alex Wang. License: CC BY 4.0.

## Contents

520 distinct ingredient IDs across 20 culinary groups. Each entry has a reviewed transparent WebP display image and an original transparent PNG. The source collection was created for Pantry Plate and is released here as an independent illustration dataset.

| Resource | Contents |
| --- | --- |
| `images/` | 520 optimized WebP files; maximum dimension 320 pixels |
| Original PNG release archive | 520 full-resolution generated PNGs; dimensions vary and are recorded per file |
| `metadata/ingredients.json` | Versioned catalog, names, groups, storage categories, paths, dimensions, byte counts, and SHA-256 hashes |
| `metadata/ingredients.csv` | The same per-image fields in a flat table |
| `metadata/prompts.json` | The recorded generation or final correction prompt for each ingredient |
| `ATTRIBUTION.md` | Suggested credit and modification notice |

The active WebPs total 9,778,818 bytes. Original PNGs total 776,725,214 bytes. ZIP archives also contain metadata and license documents, so archive sizes differ slightly. Original PNGs are distributed through GitHub Releases rather than included in Git history.

## Creation and processing

The illustrations were generated using the built-in OpenAI Codex image generation tool with transparent backgrounds. Their shared direction uses soft studio lighting, realistic food materials, a compact silhouette, and a white sticker edge. The exact underlying image model/version was not recorded; no model-specific claim is made.

Each ingredient was generated separately. An AI assistant visually reviewed all final display files against their labels; automated checks verified transparency, bounds, distinct original hashes, and file integrity. Twenty-eight content/composition corrections were resolved, such as removing unwanted bowls or garnish. Selective deterministic white-edge treatment was applied to 209 display derivatives. The corresponding PNG originals were not changed by that edge treatment. As a result, original PNGs and display WebPs can have different rims and margins.

The recorded prompts describe the final generation or corrective edit. They are provenance, not a promise of pixel-identical regeneration. The release exports only public dataset fields; local machine paths, credentials, account identifiers, and application data are excluded.

## Intended uses and limits

Suitable uses include recipe interfaces, pantry and meal-planning apps, menus, educational illustrations, design prototypes, and other visual projects that benefit from consistent ingredient artwork.

These are synthetic illustrations, not photographs, nutritional measurements, or scientific identification ground truth. Visually similar cultivars, powders, oils, and preparations may not be distinguishable from their appearance alone. The review checks observable plausibility, not botanical or chemical identity. Category labels are convenient catalog groupings, not food-storage guidance.

No train/validation/test split is supplied. This is an illustration collection, not a benchmark. If used for model development, account for its synthetic origin, common generation style, and limited visual diversity.

## License and credit

Use and adapt the collection, including commercially, under CC BY 4.0. Give appropriate credit, link the license, and indicate modifications. See [ATTRIBUTION.md](ATTRIBUTION.md) and the full [LICENSE](LICENSE). The license grants rights the publisher holds and does not claim new rights where none exist.

## Versioning and corrections

Ingredient IDs are stable within this release. Use file hashes and the `v1.0.0` release tag to pin exact versions. Report a mislabeled image or visual defect through this repository’s issues, including the ingredient ID and release version. Future corrections should ship as a new release rather than replace existing release assets silently.
