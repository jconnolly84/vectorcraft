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

# ---- Data Recovery in IndexedDB --------------------------------------------------------------
# Upstream keeps recovery copies in localStorage (about 5 MB for the whole site, shared with the
# PhotoCraft site on the same origin), which a document with a few photos overflows. The store
# below keeps them in IndexedDB instead, through an in-memory mirror (the store API is
# synchronous): reads come from the mirror, writes update it at once and are written to
# IndexedDB in order. The mirror is loaded before the app starts and refreshed every 10 s so
# other tabs' copies and heartbeats are seen. Copies already in localStorage are moved over.
# The host page's Recovery panel can switch new copies off (localStorage key
# `vectorcraft.recovery.enabled` = "false"). Without IndexedDB, the upstream store is used.

IDB = r'''

// ---- School patch: Data Recovery copies in IndexedDB (scripts/patch_vectorcraft_source.py) ----
mod idb_recovery {
    use std::collections::BTreeMap;
    use std::sync::Mutex;
    use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};

    use wasm_bindgen::JsCast as _;
    use wasm_bindgen::prelude::*;

    #[wasm_bindgen(inline_js = r#"
const PREFIX = 'vectorcraft-recovery/';
let dbp = null;
function db() {
  if (!dbp) dbp = new Promise((resolve, reject) => {
    const r = indexedDB.open('vectorcraft-recovery', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('entries');
    r.onsuccess = () => { r.result.onversionchange = () => r.result.close(); resolve(r.result); };
    r.onerror = () => reject(r.error);
    r.onblocked = () => reject(new Error('recovery storage blocked'));
  });
  return dbp;
}
async function migrate(d) {
  const keys = [];
  try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k && k.startsWith(PREFIX)) keys.push(k); } } catch { return; }
  if (!keys.length) return;
  await new Promise((resolve, reject) => {
    const t = d.transaction('entries', 'readwrite');
    const s = t.objectStore('entries');
    for (const k of keys) {
      try {
        const bin = atob(localStorage.getItem(k) || '');
        const b = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) b[i] = bin.charCodeAt(i);
        s.put(b, k.slice(PREFIX.length));
      } catch (e) { console.warn('recovery: could not move', k, e); }
    }
    t.oncomplete = resolve; t.onerror = () => reject(t.error); t.onabort = () => reject(t.error);
  });
  for (const k of keys) { try { localStorage.removeItem(k); } catch {} }
}
export async function vc_recovery_load() {
  const d = await db();
  await migrate(d);
  return await new Promise((resolve, reject) => {
    const t = d.transaction('entries', 'readonly');
    const s = t.objectStore('entries');
    const keys = s.getAllKeys(), values = s.getAll();
    t.oncomplete = () => resolve(keys.result.map((k, i) => [String(k), values.result[i]]));
    t.onerror = () => reject(t.error);
  });
}
export function vc_recovery_put(key, bytes) {
  const copy = bytes.slice();
  db().then(d => {
    const t = d.transaction('entries', 'readwrite');
    t.objectStore('entries').put(copy, key);
    t.onerror = t.onabort = () => console.warn('recovery: could not store', key, t.error);
  }).catch(e => console.warn('recovery: storage unavailable', e));
}
export function vc_recovery_delete(key) {
  db().then(d => { d.transaction('entries', 'readwrite').objectStore('entries').delete(key); })
    .catch(e => console.warn('recovery: storage unavailable', e));
}
export function vc_recovery_enabled() {
  try { return localStorage.getItem('vectorcraft.recovery.enabled') !== 'false'; } catch { return true; }
}
export function vc_sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
"#)]
    extern "C" {
        fn vc_recovery_load() -> js_sys::Promise;
        fn vc_recovery_put(key: &str, bytes: &[u8]);
        fn vc_recovery_delete(key: &str);
        fn vc_recovery_enabled() -> bool;
        fn vc_sleep(ms: i32) -> js_sys::Promise;
    }

    static MIRROR: Mutex<BTreeMap<String, Vec<u8>>> = Mutex::new(BTreeMap::new());
    /// Bumped by every write and remove: a refresh read while it changed is dropped.
    static GENERATION: AtomicU64 = AtomicU64::new(0);
    static READY: AtomicBool = AtomicBool::new(false);
    const REFRESH_MS: i32 = 10_000;

    fn mirror() -> std::sync::MutexGuard<'static, BTreeMap<String, Vec<u8>>> {
        MIRROR.lock().unwrap_or_else(std::sync::PoisonError::into_inner)
    }

    async fn fetch_all() -> Option<BTreeMap<String, Vec<u8>>> {
        let value = wasm_bindgen_futures::JsFuture::from(vc_recovery_load()).await.map_err(|e| log::warn!("recovery storage: {e:?}")).ok()?;
        let entries: js_sys::Array = value.dyn_into().ok()?;
        let mut map = BTreeMap::new();
        for entry in entries.iter() {
            let pair: js_sys::Array = entry.dyn_into().ok()?;
            let key = pair.get(0).as_string()?;
            map.insert(key, js_sys::Uint8Array::new(&pair.get(1)).to_vec());
        }
        Some(map)
    }

    /// Load the copies before the app starts, then keep the mirror fresh.
    pub async fn start() {
        let Some(map) = fetch_all().await else {
            log::warn!("recovery: IndexedDB unavailable, using local storage");
            return;
        };
        log::info!("recovery: {} entries in IndexedDB", map.len());
        *mirror() = map;
        READY.store(true, Ordering::SeqCst);
        wasm_bindgen_futures::spawn_local(async {
            loop {
                let _ = wasm_bindgen_futures::JsFuture::from(vc_sleep(REFRESH_MS)).await;
                let generation = GENERATION.load(Ordering::SeqCst);
                if let Some(map) = fetch_all().await
                    && GENERATION.load(Ordering::SeqCst) == generation
                {
                    *mirror() = map;
                }
            }
        });
    }

    pub fn list() -> Option<Vec<String>> {
        READY.load(Ordering::SeqCst).then(|| mirror().keys().cloned().collect())
    }

    pub fn read(name: &str) -> Option<Result<Vec<u8>, String>> {
        READY.load(Ordering::SeqCst).then(|| mirror().get(name).cloned().ok_or_else(|| format!("{name}: no such recovery entry")))
    }

    pub fn write(name: &str, bytes: &[u8]) -> Option<Result<(), String>> {
        if !READY.load(Ordering::SeqCst) {
            return None;
        }
        if !vc_recovery_enabled() {
            // Switched off in the host page's Recovery panel.
            return Some(Ok(()));
        }
        GENERATION.fetch_add(1, Ordering::SeqCst);
        mirror().insert(name.to_string(), bytes.to_vec());
        vc_recovery_put(name, bytes);
        Some(Ok(()))
    }

    pub fn remove(name: &str) -> Option<Result<(), String>> {
        if !READY.load(Ordering::SeqCst) {
            return None;
        }
        GENERATION.fetch_add(1, Ordering::SeqCst);
        mirror().remove(name);
        vc_recovery_delete(name);
        Some(Ok(()))
    }
}
'''

text = web_rs.read_text(encoding='utf-8')
if 'mod idb_recovery' not in text:
    web_rs.write_text(text.rstrip('\n') + '\n' + IDB, encoding='utf-8', newline='\n')

replace_once(web_rs, '        let locks = WebLocks::start(RECOVERY_PREFIX).await;\n',
             '        let locks = WebLocks::start(RECOVERY_PREFIX).await;\n'
             '        idb_recovery::start().await;\n')
replace_once(web_rs, '    fn list(&self) -> Result<Vec<String>, String> {\n        let s = local_storage()?;\n',
             '    fn list(&self) -> Result<Vec<String>, String> {\n'
             '        if let Some(names) = idb_recovery::list() {\n            return Ok(names);\n        }\n'
             '        let s = local_storage()?;\n')
replace_once(web_rs, '    fn read(&self, name: &str) -> Result<Vec<u8>, String> {\n',
             '    fn read(&self, name: &str) -> Result<Vec<u8>, String> {\n'
             '        if let Some(r) = idb_recovery::read(name) {\n            return r;\n        }\n')
replace_once(web_rs, '    fn write(&self, name: &str, bytes: &[u8]) -> Result<(), String> {\n',
             '    fn write(&self, name: &str, bytes: &[u8]) -> Result<(), String> {\n'
             '        if let Some(r) = idb_recovery::write(name, bytes) {\n            return r;\n        }\n')
replace_once(web_rs, '    fn remove(&self, name: &str) -> Result<(), String> {\n',
             '    fn remove(&self, name: &str) -> Result<(), String> {\n'
             '        if let Some(r) = idb_recovery::remove(name) {\n            return r;\n        }\n')

# Recovery copies every minute by default (upstream: 2), as on the PhotoCraft site.
replace_once(root / 'crates/engine/src/prefs.rs', '            autosave_interval: 2,\n', '            autosave_interval: 1,\n')
print('Patched VectorCraft Data Recovery to use IndexedDB, every minute.')
