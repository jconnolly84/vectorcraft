# VectorCraft for iMedia

Online VectorCraft for students: https://jconnolly84.github.io/vectorcraft/

- **Editor:** the official [storytold/vectorcraft](https://github.com/storytold/vectorcraft) v0.24.1
  web release, rebuilt with one small patch so it also loads the school font library.
- **Fonts:** the same 148 font families (270 faces) as the PhotoCraft site, in `font-library/`
  with their licences. They load in the background when the editor opens and appear in
  VectorCraft's font menus.
- **Top toolbar:** Recovery, Fonts & import (load .ttf/.otf files, use fonts installed on this PC, browse
  the library by category), Full screen, and Hide/Show tools.

Work stays in the browser: nothing is uploaded. Save/export (download) work before closing the
tab.

## Student first view

`scripts/patch_student_layout.py` makes the first view less intimidating for students new to
vector software:

- **Toolbar (20 everyday tools, Illustrator Basic-toolbar groups):** Selection; Direct Selection;
  Rectangle (+ Rounded Rectangle); Ellipse; Polygon (+ Star); Line (+ Arc, Spiral); Pen (+ add /
  delete / anchor point); Curvature; Pencil (+ Smooth); Paintbrush (+ Blob Brush); Eraser (+
  Scissors, Knife); Rotate (+ Reflect); Scale (+ Shear); Shape Builder (+ Live Paint Bucket);
  Type (+ Type on a Path, Area Type); Eyedropper; Gradient; Hand; Zoom. Tools in brackets are in
  the button's flyout (press and hold).
- **Hidden, not removed:** the toolbar's **•••** button opens the All Tools drawer with every
  other tool (drag one onto the toolbar to keep it); Window → Toolbars → Advanced shows them all.
  Edit Toolbar → Reset returns to the classroom set.
- **Panels:** Properties on top (it changes with what is selected: fill, stroke, align,
  pathfinder) and **Layers open beneath it**. The icon column has only Color, Swatches, Stroke,
  Gradient, Transparency, Align, Pathfinder, Character, Paragraph and History. Every other panel
  is in the Window menu. Window → Workspace → Reset Essentials returns to this layout.

## Recovery

VectorCraft's own Data Recovery saves a copy of every changed document about every minute and,
after a browser or tab crash, offers them in a Recover Documents dialog when the page is opened
again. The custom build keeps these copies in this site's IndexedDB (`vectorcraft-recovery`)
instead of upstream's `localStorage`, which only holds about 5 MB for the whole site and would
overflow with a few photos. The toolbar's **Recovery** panel (`host/recovery.js`) turns copies on
or off, shows what is protected, reloads the editor to recover copies a crashed tab left behind,
asks the browser to protect the storage, and clears old copies. Copies stay in that browser
profile only; school profile cleanup or private browsing can erase them.

## How it is built

1. **Build workflow** (`.github/workflows/build-custom-vectorcraft.yml`, run by hand): checks out
   the official v0.24.1 source and the same craft-fonts commit as the official release, applies
   `scripts/patch_vectorcraft_source.py`, and builds with the upstream `packaging/web/package.sh`.
   The patch adds a loader that reads `fonts/manifest.txt` next to the app and adds each listed
   face (checked against its SHA-256) to the font database, moves Data Recovery to IndexedDB and
   makes its default interval 1 minute.
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
