"""Stage the GitHub Pages site in _site/: the checksum-verified custom build at /vectorcraft/,
the school font library beside it and the host page (toolbar) at the root."""
from pathlib import Path
import hashlib
import json
import re
import shutil

root = Path(__file__).resolve().parents[1]
site = root / '_site'
if site.exists():
    raise SystemExit('Use a fresh _site directory to avoid stale files.')

# 1. The compiled app, exactly as the build workflow produced it.
source = root / 'custom-build/web'
metadata = json.loads((root / 'custom-build/BUILD.json').read_text(encoding='utf-8'))
actual = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
assert actual == set(metadata['files']), 'Custom build file set differs from BUILD.json'
for relative, digest in metadata['files'].items():
    assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == digest, relative
target = site / 'vectorcraft'
shutil.copytree(source, target)

# 2. The school font library (same files as PhotoCraft), served at vectorcraft/fonts/.
library = root / 'font-library'
families = set()
manifest_rows = []
for line in (library / 'fonts/manifest.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.startswith('#'):
        continue
    family, style, path, scripts, license_id, license_path, expected, url = map(str.strip, line.split('|'))
    for rel in (path, license_path):
        assert rel.startswith('fonts/') and '..' not in Path(rel).parts
        assert (library / rel).is_file(), f'Missing font asset: {rel}'
    assert license_id in ('OFL-1.1', 'Apache-2.0', 'CC0-1.0'), license_id
    assert hashlib.sha256((library / path).read_bytes()).hexdigest() == expected, path
    families.add(family)
    manifest_rows.append(line)
for item in (library / 'fonts').iterdir():
    destination = target / 'fonts' / item.name
    assert not destination.exists(), f'Font library would overwrite release file: {item.name}'
    (shutil.copytree if item.is_dir() else shutil.copyfile)(item, destination)
print(f'Verified and staged {len(families)} font families ({len(manifest_rows)} faces) with licences.')

# 3. Host page and toolbar scripts.
(site / '.nojekyll').touch()
for asset in (root / 'host').iterdir():
    if asset.is_file():
        shutil.copyfile(asset, site / asset.name)
font_worker, font_host = site / 'local-font-worker.js', site / 'local-fonts.js'
font_host.write_text(font_host.read_text(encoding='utf-8').replace(
    '__FONT_WORKER_VERSION__', hashlib.sha256(font_worker.read_bytes()).hexdigest()[:12]), encoding='utf-8')
index = site / 'index.html'
html = index.read_text(encoding='utf-8')
for script in site.glob('*.js'):
    digest = hashlib.sha256(script.read_bytes()).hexdigest()[:12]
    html = re.sub(r'src="\./' + re.escape(script.name) + r'(?:\?[^"]*)?"', f'src="./{script.name}?v={digest}"', html)
index.write_text(html, encoding='utf-8')
print(f'Staged VectorCraft build from workflow run {metadata["workflow_run"]}.')
