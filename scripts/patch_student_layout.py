"""Beginner-friendly first view for students new to vector software (like Illustrator).

1. Basic toolbar (VectorCraft's default) trimmed from 29 slots to 20 everyday tools, grouped as
   Illustrator's Basic toolbar groups them. Every other tool is still one click away: the toolbar's
   ••• button opens the All Tools drawer (hidden tools listed under their headings and "More",
   drag one onto the toolbar to keep it), and Window → Toolbars → Advanced shows the full set.
   Edit Toolbar → Reset returns to this classroom set.
2. Panels: Properties (the context-aware panel Illustrator recommends to beginners) stays at the
   top of the dock and Layers is shown open beneath it (Libraries is a tab beside Layers). The
   icon column keeps only the panels students use: Color, Swatches, Stroke, Gradient,
   Transparency, Align, Pathfinder, Character, Paragraph and History. Every other panel is in the
   Window menu and docks beside its usual neighbours when opened.

Only defaults change: a workspace a student customizes, or a toolbar they edit, is kept.
Usage: python scripts/patch_student_layout.py <vectorcraft checkout>
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    if new in text:
        return
    assert text.count(old) == 1, f'{path}: expected exactly one match for {old[:70]!r}'
    path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')


# ---- 1. Basic toolbar ----
toolbar = root / 'crates/ui-egui/src/toolbar.rs'
text = toolbar.read_text(encoding='utf-8')
STUDENT_BASIC = '''pub const BASIC: &[(&str, &[&[&str]])] = &[
    // School build (scripts/patch_student_layout.py): the everyday tools only; the rest are in the
    // ••• All Tools drawer and the Advanced toolbar.
    ("Select", &[&["selection"], &["directSelection", "groupSelection"]]),
    ("Shapes", &[&["rectangle", "roundedRectangle"], &["ellipse"], &["polygon", "star"], &["lineSegment", "arc", "spiral"]]),
    (
        "Draw",
        &[
            &["pen", "addAnchor", "deleteAnchor", "anchorPoint"],
            &["curvature"],
            &["pencil", "smooth"],
            &["paintbrush", "blobBrush"],
            &["eraser", "scissors", "knife"],
        ],
    ),
    ("Modify", &[&["rotate", "reflect"], &["scale", "shear"], &["shapeBuilder", "livePaintBucket"]]),
    ("Type", &[&["type", "typeOnPath", "areaType"]]),
    ("Color", &[&["eyedropper"], &["gradient"]]),
    ("Navigate", &[&["hand"], &["zoom"]]),
];
'''
if 'patch_student_layout.py' not in text:
    match = re.search(r'pub const BASIC: &\[\(&str, &\[&\[&str\]\]\)\] = &\[\n.*?\n\];\n', text, re.S)
    assert match, 'BASIC toolbar not found'
    # Every tool named must be one the upstream Basic toolbar already had.
    upstream_ids = set(re.findall(r'"([a-zA-Z]+)"', match.group(0)))
    ours = set(re.findall(r'"([a-zA-Z]+)"', STUDENT_BASIC.split('];')[0].split('= &[', 1)[1]))
    assert ours <= upstream_ids, f'Unknown tool ids: {sorted(ours - upstream_ids)}'
    toolbar.write_text(text[:match.start()] + STUDENT_BASIC + text[match.end():], encoding='utf-8', newline='\n')

# ---- 2. Default dock ----
docking = root / 'crates/ui-egui/src/panel_docking.rs'
replace_once(docking, '''    let active = panels.iter().position(|p| p == tab.info().0).unwrap_or(0);
    let mut columns = Vec::new();
    if !panels.is_empty() {
        columns.push(Column {
            groups: vec![Group::new(panels, active)],''', '''    // School build (scripts/patch_student_layout.py): Properties on top, Layers open beneath it.
    let (top, below): (Vec<String>, Vec<String>) = panels.iter().cloned().partition(|p| p != "layers" && p != "libraries");
    let active = top.iter().position(|p| p == tab.info().0).unwrap_or(0);
    let mut main_groups = Vec::new();
    if !top.is_empty() {
        main_groups.push(Group::new(top, active));
    }
    if !below.is_empty() {
        let layers = below.iter().position(|p| p == "layers").unwrap_or(0);
        main_groups.push(Group::new(below, layers));
    }
    let mut columns = Vec::new();
    if !panels.is_empty() {
        columns.push(Column {
            groups: main_groups,''')
replace_once(docking, '''    let groups: Vec<Group<String>> = ICON_PANEL_GROUPS.iter().filter_map(|g| placed.group(g)).collect();''',
             '''    let groups: Vec<Group<String>> = STUDENT_ICON_GROUPS.iter().filter_map(|g| placed.group(g)).collect();''')
text = docking.read_text(encoding='utf-8')
if 'STUDENT_ICON_GROUPS: ' not in text:
    docking.write_text(text.rstrip('\n') + '''

/// School build: the icon column's panels in a new workspace (every panel stays in the Window menu).
const STUDENT_ICON_GROUPS: &[&[&str]] =
    &[&["color", "swatches"], &["stroke", "gradient", "transparency"], &["align", "pathfinder"], &["character", "paragraph"], &["history"]];
''', encoding='utf-8', newline='\n')
print('Patched the student toolbar and panel defaults.')
