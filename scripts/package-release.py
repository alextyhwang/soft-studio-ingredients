"""Build and verify the versioned dataset release archives (Python standard library)."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent.parent
config = json.loads((ROOT / 'dataset.json').read_text(encoding='utf-8'))
catalog = json.loads((ROOT / 'metadata/ingredients.json').read_text(encoding='utf-8'))
assert config['license'] == 'CC-BY-4.0', 'Confirm the dataset license before packaging.'
assert catalog['count'] == len(catalog['items']) == config['ingredientCount'] == 812
recipes = json.loads((ROOT / 'metadata/recipes.json').read_text(encoding='utf-8'))
assert recipes['count'] == len(recipes['items']) == config['recipeCount'] == 809
output = ROOT / '.release/artifacts'
output.mkdir(parents=True, exist_ok=True)
documents = ['LICENSE', 'ATTRIBUTION.md', 'DATASET_CARD.md', 'metadata/ingredients.json', 'metadata/ingredients.csv', 'metadata/prompts.json']

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def add_bytes(archive, name, data, compress=False):
    info = zipfile.ZipInfo(name, date_time=(2026, 10, 2, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED if compress else zipfile.ZIP_STORED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)

artifacts = []
for extension, archive_key, directory in [('webp', 'webpArchive', ROOT/'images'), ('png', 'pngArchive', ROOT/'.release/originals'), ('webp', 'recipeArchive', ROOT/'images')]:
    destination = output/config[archive_key]
    included_documents = documents + (['RECIPE_SOURCES.md', 'metadata/recipes.json', 'metadata/ingredient-mapping.json'] if archive_key == 'recipeArchive' else [])
    with zipfile.ZipFile(destination, 'w', allowZip64=True) as archive:
        for item in catalog['items']:
            source = directory/f"{item['id']}.{extension}"
            data = source.read_bytes()
            assert len(data) == item[extension]['bytes'], source
            assert hashlib.sha256(data).hexdigest() == item[extension]['sha256'], source
            add_bytes(archive, item[extension]['path'], data)
        for name in included_documents:
            add_bytes(archive, name, (ROOT/name).read_bytes(), compress=True)
    with zipfile.ZipFile(destination) as archive:
        assert len(archive.namelist()) == catalog['count'] + len(included_documents)
        assert archive.testzip() is None
        assert not any(name.startswith('/') or '..' in Path(name).parts for name in archive.namelist())
    artifacts.append(destination)
    print(json.dumps({'archive': destination.name, 'images':catalog['count'], 'recipes':recipes['count'] if archive_key == 'recipeArchive' else 0, 'bytes':destination.stat().st_size, 'sha256':digest(destination)}), flush=True)

for name in ['ingredients.json', 'ingredients.csv', 'prompts.json', 'recipes.json', 'ingredient-mapping.json']:
    destination = output/name
    shutil.copyfile(ROOT/'metadata'/name, destination)
    artifacts.append(destination)
(output/'SHA256SUMS.txt').write_text(''.join(f'{digest(path)}  {path.name}\n' for path in artifacts), encoding='utf-8')
print('Release files verified; SHA256SUMS.txt written.', flush=True)
