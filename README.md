# VectorCraft for iMedia

Online VectorCraft for students: https://jconnolly84.github.io/vectorcraft/

- **Editor:** the official [storytold/vectorcraft](https://github.com/storytold/vectorcraft) v0.24.1
  web release, rebuilt with one small patch so it also loads the school font library.
- **Fonts:** the same 148 font families (270 faces) as the PhotoCraft site, in `font-library/`
  with their licences. They load in the background when the editor opens and appear in
  VectorCraft's font menus.
- **Top toolbar:** Fonts & import (load .ttf/.otf files, use fonts installed on this PC, browse
  the library by category), Full screen, and Hide/Show tools.

Work stays in the browser: nothing is uploaded. Save/export (download) work before closing the
tab. VectorCraft keeps its own recovery copies in the browser after a crash.

## How it is built

1. **Build workflow** (`.github/workflows/build-custom-vectorcraft.yml`, run by hand): checks out
   the official v0.24.1 source and the same craft-fonts commit as the official release, applies
   `scripts/patch_vectorcraft_source.py`, and builds with the upstream `packaging/web/package.sh`.
   The patch adds a loader that reads `fonts/manifest.txt` next to the app and adds each listed
   face (checked against its SHA-256) to the font database.
2. **Import:** `gh run download <run> -n vectorcraft-custom-web -D <dir>` then
   `python scripts/import_custom_build.py <dir>`, and commit `custom-build/`.
3. **Pages workflow** (`.github/workflows/vectorcraft-pages.yml`, on push): verifies every build
   file and font against its checksum, stages the app at `/vectorcraft/`, the font library at
   `/vectorcraft/fonts/` and the toolbar page at `/`.

## Fonts from this PC / font files

The toolbar's service worker (`host/local-font-worker.js`) adds PC fonts or chosen font files to
`vectorcraft/fonts/manifest.txt` for that editor session only, and serves their bytes from the
page's memory. Applying them restarts the editor, so save first. PC fonts need desktop Chrome or
Edge.

## Upgrading

Change `UPSTREAM_REF` (and `CRAFT_FONTS_REF` to the one the new release's workflow uses) and the
version numbers in the build workflow, run it, then import and commit the new build.

The official `SHA256SUMS.txt` of v0.24.1 is kept in `vendor/vectorcraft/`.
