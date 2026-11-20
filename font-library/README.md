# Fonts for the PhotoCraft web host

148 families / 270 font files. Fonts load on demand
through PhotoCraft's supported `fonts/manifest.txt`; they are not added to Wasm.
Every family retains its licence beside its files. No proprietary Windows fonts
are included. Font names are the fonts' real internal names, not Microsoft aliases.

## Familiar Office alternatives

| Windows font | Choose this family |
| --- | --- |
| Arial | Liberation Sans |
| Times New Roman | Liberation Serif |
| Courier New | Liberation Mono |
| Calibri | Carlito |
| Cambria | Caladea |

These are metric-compatible substitutes, not identical font designs. Existing
documents requesting Microsoft family names may require manual font selection.
Inkscape uses installed fonts; it does not define a universal font collection.
These open fonts can also be installed on Windows for use in Inkscape.

## Selection

- Blackletter: UnifrakturCook, UnifrakturMaguntia, Pirata One, Grenze Gotisch,
  New Rocker and Germania One, plus Fruktur, Astloch, Jolly Lodger, Jacquard 12,
  Jacquard 24, Jacquarda Bastarda 9 and MedievalSharp. These are from the pinned Google Fonts source,
  retain their SIL OFL licences, and appear in the native Blackletter category.

- Everyday and editorial: Inter, Lato, Montserrat, Open Sans, Roboto, Poppins,
  Nunito Sans, Source Sans 3, Source Serif 4, Merriweather, Playfair Display,
  Raleway, Rubik, Quicksand, Comfortaa, Cormorant Garamond, Cinzel.
- Bold poster styles: Anton, Bebas Neue, Oswald, Archivo Black, Alfa Slab One,
  Abril Fatface, Bangers, Bungee, Black Ops One, Chewy, Luckiest Guy, Righteous.
- Script and handwriting: Dancing Script, Great Vibes, Lobster, Pacifico,
  Satisfy, Sacramento, Caveat, Indie Flower, Permanent Marker,
  Shadows Into Light, Amatic SC, Courgette, Patrick Hand, Kalam.
- Decorative, retro and technology: Special Elite, Rye, Creepster, Monoton,
  Orbitron, Press Start 2P, Audiowide, Fredericka the Great.

The manifest lists the exact families, available styles, hashes and sources.
Variable fonts offer weight choices through their weight axis. Character coverage
varies: this is primarily a Latin design catalog, not complete worldwide coverage.

## Expanded sections

| Section | Families | Examples added |
| --- | ---: | --- |
| Serif | 17 | Lora, EB Garamond, Bodoni Moda, Libre Baskerville |
| Slab Serif | 13 | Arvo, Bitter, Roboto Slab, Zilla Slab |
| Sans Serif | 26 | DM Sans, Manrope, Outfit, Space Grotesk |
| Script | 15 | Allura, Alex Brush, Parisienne, Yellowtail |
| Monospace | 15 | JetBrains Mono, Fira Code, IBM Plex Mono, Source Code Pro |
| Handwritten | 17 | Architects Daughter, Handlee, Schoolbell, Rock Salt |
| Blackletter | 13 | Fruktur, Astloch, Jacquard 12, MedievalSharp |
| Decorative | 32 | Rubik Glitch, Nosifer, Rampart One, Zen Tokyo Zoo |

The 76 additional families retain their complete OFL or Apache licences and
unmodified TTFs, including variable faces. `EXPANDED-SOURCES.json` records the
pinned upstream commit, exact download URLs, SHA256s, licence and category.
`scripts/import_more_fonts.py` also verifies every downloaded Git blob against
the official repository's pinned tree. Its entries survive a base-catalog
reimport; run `scripts/build_font_catalog.py` afterwards. Rebuild the native app
when categories change so the menu filters classify unloaded fonts too.

Build 43709610447 packages this catalog. The exact native classification
helpers and menu filters passed all three focused tests for all 148 families;
the font metadata/import tests passed all 270 faces. Static staging verified
every font hash and licence path. A separate Chrome preview verified new fonts
under Monospace and Blackletter, plus JetBrains Mono rendering in the native
picker preview and a text layer. Fonts are served from the same Pages site.

## Provenance and maintenance

### Decorative fonts from DaFont

Added Star Minor, Speed Freak, Help Me, Blackcraft, Neon Sans, Glitch Goblin,
Drybrush, Bad Comic, Bubblez Graffiti and Westhorn (14 faces across 10 families).
Speed Freak is by Tup Wanders; the other nine are by GGBotNet. These downloads
include explicit SIL OFL or CC0 licence texts, retained unmodified beside the
font files. `DAFONT-SOURCES.json` records each listing/download URL, archive hash,
font hashes, licence hash and category. `dafont-manifest.txt` retains their manifest
entries. Fonts marked only "free for personal use" were not selected.

Run `python scripts/import_dafont_fonts.py` to reimport these selections. Unlike
the pinned GitHub catalogs, DaFont download URLs may change their contents;
review archive/hash changes before publishing an update. The main font importer
preserves these additional entries when rebuilding its base catalog.

Font files come from the official `storytold/craft-fonts` Latin catalog and
`google/fonts`, at pinned commits recorded in `SOURCES.json`. Craft catalog
checksums were verified against its published manifest. Base-catalog file hashes
(including licences) are recorded in SOURCES.json; expanded and DaFont assets
have their own source records described above. Deployment checks font hashes,
licence paths and manifest completeness before publishing.

`python scripts/import_fonts.py` recreates the catalog (requires fontTools and gh).
Normal deployment uses the checked-in files and needs no font tooling or downloads.

Microsoft licensing: https://learn.microsoft.com/en-us/typography/fonts/font-faq
Inkscape fonts: https://wiki.inkscape.org/wiki/Installing_fonts
