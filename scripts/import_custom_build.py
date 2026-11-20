"""Import a downloaded `vectorcraft-custom-web` artifact into custom-build/.

    gh run download <run id> -n vectorcraft-custom-web -D <empty folder>
    python scripts/import_custom_build.py <that folder>
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
artifact = Path(sys.argv[1])
build = json.loads((artifact / 'BUILD.json').read_text(encoding='utf-8'))
zip_path = artifact / f"vectorcraft-web-{build['version']}.zip"
prefix = f"vectorcraft-web-{build['version']}/"

target = root / 'custom-build'
if target.exists():
    shutil.rmtree(target)
web = target / 'web'
web.mkdir(parents=True)
files = {}
with zipfile.ZipFile(zip_path) as archive:
    for info in archive.infolist():
        if info.is_dir():
            continue
        assert info.filename.startswith(prefix), info.filename
        relative = info.filename[len(prefix):]
        assert relative and '..' not in Path(relative).parts and not Path(relative).is_absolute(), relative
        data = archive.read(info)
        out = web / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        files[relative] = hashlib.sha256(data).hexdigest()
build['zip_sha256'] = hashlib.sha256(zip_path.read_bytes()).hexdigest()
build['files'] = dict(sorted(files.items()))
(target / 'BUILD.json').write_text(json.dumps(build, indent=2) + '\n', encoding='utf-8')
shutil.copyfile(artifact / 'vectorcraft-source.patch', target / 'source.patch')
print(f'Imported {len(files)} files from workflow run {build["workflow_run"]}.')
