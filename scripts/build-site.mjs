import { createHash } from "node:crypto";
import {
  copyFileSync,
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const config = JSON.parse(readFileSync(resolve(root, "dataset.json"), "utf8"));
const catalog = JSON.parse(
  readFileSync(resolve(root, "metadata/ingredients.json"), "utf8"),
);
const dist = resolve(root, "dist");
mkdirSync(resolve(dist, "images"), { recursive: true });
if (catalog.items.length !== 520) throw new Error("Expected 520 ingredients.");
const items = catalog.items.map((item) => {
  const bytes = readFileSync(resolve(root, item.webp.path));
  const hash = createHash("sha256").update(bytes).digest("hex");
  if (hash !== item.webp.sha256) throw new Error(`Artwork changed: ${item.id}`);
  const image = `images/${item.id}.${hash.slice(0, 12)}.webp`;
  writeFileSync(resolve(dist, image), bytes);
  return { id: item.id, name: item.name, group: item.group, image };
});
const schema = {
  "@context": "https://schema.org",
  "@type": "Dataset",
  name: config.name,
  description:
    "520 AI-generated ingredient illustrations with transparent backgrounds, available as optimized WebP files and original PNGs, with category labels and CSV/JSON metadata.",
  url: config.site,
  version: config.version,
  identifier: config.github,
  creator: {
    "@type": "Person",
    name: config.author,
    url: "https://github.com/alextyhwang",
  },
  keywords: [
    "ingredient illustrations",
    "food illustration dataset",
    "transparent food assets",
    "AI-generated images",
  ],
  ...(config.license ? { license: config.licenseUrl } : {}),
  distribution: [
    {
      "@type": "DataDownload",
      encodingFormat: "application/zip",
      name: "WebP images",
      contentUrl: `${config.releaseBase}/${config.webpArchive}`,
    },
    {
      "@type": "DataDownload",
      encodingFormat: "application/zip",
      name: "Original PNG images",
      contentUrl: `${config.releaseBase}/${config.pngArchive}`,
    },
    {
      "@type": "DataDownload",
      encodingFormat: "text/csv",
      contentUrl: `${config.site}/metadata/ingredients.csv`,
    },
  ],
};
const ogImage = `${config.site}/${items.find((item) => item.id === "bok-choy").image}`;
const replacements = {
  SITE: config.site,
  GITHUB: config.github,
  VERSION: config.version,
  WEBP_DOWNLOAD: `${config.releaseBase}/${config.webpArchive}`,
  PNG_DOWNLOAD: `${config.releaseBase}/${config.pngArchive}`,
  LICENSE_NAME: config.licenseName,
  LICENSE_URL: config.licenseUrl,
  LICENSE_SUMMARY: config.licenseSummary,
  DATASET_SCHEMA: JSON.stringify(schema).replaceAll("<", "\\u003c"),
  OG_IMAGE: ogImage,
};
let html = readFileSync(resolve(root, "site/index.html"), "utf8");
for (const [key, value] of Object.entries(replacements))
  html = html.replaceAll(`{{${key}}}`, value);
if (/\{\{[A-Z_]+\}\}/.test(html))
  throw new Error("Unresolved page template token.");
writeFileSync(resolve(dist, "index.html"), html);
for (const file of ["styles.css", "app.js"])
  copyFileSync(resolve(root, "site", file), resolve(dist, file));
if (existsSync(resolve(root, "site/launch")))
  cpSync(resolve(root, "site/launch"), resolve(dist, "launch"), {
    recursive: true,
  });
writeFileSync(resolve(dist, "ingredients.json"), JSON.stringify(items));
mkdirSync(resolve(dist, "metadata"), { recursive: true });
for (const file of ["ingredients.json", "ingredients.csv", "prompts.json"])
  copyFileSync(
    resolve(root, "metadata", file),
    resolve(dist, "metadata", file),
  );
for (const file of ["LICENSE", "DATASET_CARD.md", "ATTRIBUTION.md"]) {
  if (existsSync(resolve(root, file)))
    copyFileSync(resolve(root, file), resolve(dist, file));
}
writeFileSync(
  resolve(dist, "robots.txt"),
  `User-agent: *\nAllow: /\nSitemap: ${config.site}/sitemap.xml\n`,
);
writeFileSync(
  resolve(dist, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>${config.site}/</loc></url></urlset>\n`,
);
writeFileSync(
  resolve(dist, "vercel.json"),
  JSON.stringify(
    {
      $schema: "https://openapi.vercel.sh/vercel.json",
      framework: null,
      buildCommand: "",
      installCommand: "",
      outputDirectory: ".",
      cleanUrls: true,
      headers: [
        {
          source: "/images/(.*)",
          headers: [
            {
              key: "Cache-Control",
              value: "public, max-age=31536000, immutable",
            },
          ],
        },
        {
          source: "/(.*)",
          headers: [
            { key: "X-Content-Type-Options", value: "nosniff" },
            {
              key: "Referrer-Policy",
              value: "strict-origin-when-cross-origin",
            },
          ],
        },
      ],
    },
    null,
    2,
  ),
);
console.log(
  JSON.stringify({
    images: items.length,
    output: dist,
    license: config.license,
  }),
);
