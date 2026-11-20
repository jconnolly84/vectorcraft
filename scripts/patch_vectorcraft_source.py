"""Patch an official VectorCraft checkout so its web build also loads the school font library.

The patch adds one loader beside the upstream web-font loader: it reads `fonts/manifest.txt`
(served next to the app; `family | style | file | ... | sha256 | ...`, the font-library format),
fetches each listed face in the background and adds it to the app's font database. Rows with a
64-digit SHA-256 in column 7 are checked with Subresource Integrity. Usage:

    python scripts/patch_vectorcraft_source.py <vectorcraft checkout>
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
fonts_rs = root / 'apps/vectorcraft-web/src/fonts.rs'
web_rs = root / 'apps/vectorcraft-web/src/web.rs'


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    if new in text:
        return
    assert text.count(old) == 1, f'{path}: expected exactly one match for {old!r}'
    path.write_text(text.replace(old, new), encoding='utf-8', newline='\n')


# fetch(): integrity becomes optional (the PC/imported fonts the host page adds have none).
replace_once(fonts_rs, '    let bytes = match fetch(f.url, f.integrity, timeout_ms).await {',
             '    let bytes = match fetch(f.url, Some(f.integrity), timeout_ms).await {')
replace_once(fonts_rs, 'async fn fetch(url: &str, integrity: &str, timeout_ms: i32)',
             'async fn fetch(url: &str, integrity: Option<&str>, timeout_ms: i32)')
replace_once(fonts_rs, '    init.set_integrity(integrity);\n',
             '    if let Some(integrity) = integrity {\n        init.set_integrity(integrity);\n    }\n')

LIBRARY = r'''
// ---- School font library (added by jconnolly84/vectorcraft's scripts/patch_vectorcraft_source.py) ----

/// Library faces fetched at once.
const LIBRARY_PARALLEL: usize = 6;

thread_local! {
    static LIBRARY_STARTED: Cell<bool> = const { Cell::new(false) };
}

/// One face from `fonts/manifest.txt`.
struct LibraryFont {
    family: String,
    style: String,
    url: String,
    integrity: Option<String>,
}

/// Parse `family | style | file | scripts | licence | licence file | sha256 | source` rows (only the
/// first three are required). Files must be relative paths under `fonts/`.
fn parse_library(text: &str) -> Vec<LibraryFont> {
    text.lines()
        .map(str::trim)
        .filter(|l| !l.is_empty() && !l.starts_with('#'))
        .filter_map(|l| {
            let f: Vec<&str> = l.split('|').map(str::trim).collect();
            let (family, style, url) = (*f.first()?, *f.get(1)?, *f.get(2)?);
            if family.is_empty() || !url.starts_with("fonts/") || url.contains("..") || url.contains("://") {
                return None;
            }
            let integrity = f.get(6).and_then(|sha| vectorcraft_text_sri(sha));
            Some(LibraryFont { family: family.into(), style: style.into(), url: url.into(), integrity })
        })
        .collect()
}

/// `sha256-<base64>` for a 64-digit hex SHA-256.
fn vectorcraft_text_sri(hex: &str) -> Option<String> {
    use base64_lite as b64;
    if hex.len() != 64 {
        return None;
    }
    let bytes: Option<Vec<u8>> = (0..32).map(|i| hex.get(2 * i..2 * i + 2).and_then(|h| u8::from_str_radix(h, 16).ok())).collect();
    Some(format!("sha256-{}", b64::encode(&bytes?)))
}

mod base64_lite {
    pub fn encode(data: &[u8]) -> String {
        const T: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        let mut s = String::with_capacity(data.len().div_ceil(3) * 4);
        for chunk in data.chunks(3) {
            let b = |i: usize| u32::from(chunk.get(i).copied().unwrap_or(0));
            let n = (b(0) << 16) | (b(1) << 8) | b(2);
            for k in 0..4 {
                if k <= chunk.len() {
                    s.push(char::from(T[((n >> (18 - 6 * k)) & 63) as usize]));
                } else {
                    s.push('=');
                }
            }
        }
        s
    }
}

/// Fetch `fonts/manifest.txt` and every face it lists, [`LIBRARY_PARALLEL`] at a time, asking `ctx`
/// for a frame after each so the font menus pick it up. A missing manifest does nothing. Only the
/// first call does anything.
pub fn spawn_library_fonts(ctx: egui::Context) {
    if LIBRARY_STARTED.with(|s| s.replace(true)) {
        return;
    }
    wasm_bindgen_futures::spawn_local(async move {
        let text = match fetch("fonts/manifest.txt", None, STARTUP_TIMEOUT_MS).await {
            Ok(bytes) => String::from_utf8_lossy(&bytes).into_owned(),
            Err(e) => {
                log::info!("school font library: {e}");
                return;
            }
        };
        let queue = Rc::new(parse_library(&text));
        log::info!("school font library: {} faces", queue.len());
        let next = Rc::new(Cell::new(0usize));
        for _ in 0..LIBRARY_PARALLEL.min(queue.len()) {
            let (queue, next, ctx) = (queue.clone(), next.clone(), ctx.clone());
            wasm_bindgen_futures::spawn_local(async move {
                loop {
                    let i = next.get();
                    next.set(i + 1);
                    let Some(f) = queue.get(i) else { break };
                    match fetch(&f.url, f.integrity.as_deref(), BACKGROUND_TIMEOUT_MS).await {
                        Ok(bytes) => {
                            if FontDb::global().add_font(bytes) == 0 {
                                log::warn!("library font {} {}: not a font, or already loaded", f.family, f.style);
                            } else {
                                ctx.request_repaint();
                            }
                        }
                        Err(e) => log::warn!("library font {} {}: {e}", f.family, f.style),
                    }
                }
            });
        }
    });
}
'''

text = fonts_rs.read_text(encoding='utf-8')
if 'spawn_library_fonts' not in text:
    fonts_rs.write_text(text.rstrip('\n') + '\n' + LIBRARY, encoding='utf-8', newline='\n')

replace_once(web_rs, '                crate::fonts::spawn_background_fonts(ctx.clone());\n',
             '                crate::fonts::spawn_background_fonts(ctx.clone());\n'
             '                crate::fonts::spawn_library_fonts(ctx.clone());\n')
print('Patched VectorCraft web font loading for the school font library.')
