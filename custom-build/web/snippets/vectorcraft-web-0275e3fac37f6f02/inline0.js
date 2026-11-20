
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
