"""Build an explicit design-category catalog, independent of incomplete font metadata."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    'Blackletter': 'UnifrakturCook|UnifrakturMaguntia|Pirata One|Grenze Gotisch|New Rocker|Germania One',
    'Serif': 'Abril Fatface|Caladea|Cinzel|Cormorant Garamond|Liberation Serif|Merriweather|Playfair Display|Source Serif 4',
    'Slab Serif': 'Alfa Slab One|Rye',
    'Sans Serif': 'Anton|Archivo Black|Bebas Neue|Carlito|Comfortaa|Inter|Lato|Liberation Sans|Montserrat|Nunito Sans|Open Sans|Oswald|Poppins|Quicksand|Raleway|Roboto|Rubik|Source Sans 3',
    'Script': 'Courgette|Dancing Script|Great Vibes|Lobster|Pacifico|Sacramento|Satisfy',
    'Monospace': 'Liberation Mono',
    'Handwritten': 'Amatic SC|Caveat|Indie Flower|Kalam|Patrick Hand|Permanent Marker|Shadows Into Light',
    'Decorative': 'Audiowide|Bangers|Black Ops One|Bungee|Chewy|Creepster|Fredericka the Great|Luckiest Guy|Monoton|Orbitron|Press Start 2P|Righteous|Special Elite',
}
catalog = [{'family': family, 'category': category}
           for category, names in GROUPS.items() for family in names.split('|')]
for extra in (ROOT / 'font-library/DAFONT-SOURCES.json', ROOT / 'font-library/EXPANDED-SOURCES.json'):
    if extra.exists():
        for source in json.loads(extra.read_text(encoding='utf-8')):
            catalog.extend({'family': family, 'category': source['category']} for family in source['families'])
families = {line.split('|')[0].strip() for line in (ROOT / 'font-library/fonts/manifest.txt').read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.startswith('#')}
assert len(catalog) == len({font['family'] for font in catalog}), 'Duplicate catalog family'
assert families == {font['family'] for font in catalog}, 'Catalog must cover every hosted family exactly once'
catalog.sort(key=lambda font: font['family'].casefold())
(ROOT / 'host/font-catalog.json').write_text(json.dumps(catalog, indent=2) + '\n', encoding='utf-8')
print(f'Categorized all {len(catalog)} hosted font families.')
