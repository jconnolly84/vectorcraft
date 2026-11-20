/* Recovery panel for VectorCraft's own Data Recovery. On-device only: no fetch or upload.
   The editor (custom build) writes recovery copies of changed documents to this site's IndexedDB
   database `vectorcraft-recovery` every minute and offers them in a Recover Documents dialog when
   it next opens. Each editor tab holds a Web Lock named `vectorcraft-recovery/<area>` while it runs. */
(() => {
  const DB = 'vectorcraft-recovery', STORE = 'entries', LOCK_PREFIX = 'vectorcraft-recovery/';
  const ENABLED_KEY = 'vectorcraft.recovery.enabled';
  const panel = document.getElementById('recovery-tools');
  const box = document.getElementById('recovery-enabled');
  const status = document.getElementById('recovery-status');
  const available = document.getElementById('recovery-available');
  const reload = document.getElementById('recovery-reload');
  const keep = document.getElementById('recovery-keep');
  const clear = document.getElementById('recovery-clear');
  const frame = document.getElementById('editor');

  const isEnabled = () => { try { return localStorage.getItem(ENABLED_KEY) !== 'false'; } catch { return true; } };
  box.checked = isEnabled();
  box.addEventListener('change', () => {
    try { localStorage.setItem(ENABLED_KEY, box.checked ? 'true' : 'false'); } catch { /* storage blocked */ }
    refresh();
  });

  function open() {
    return new Promise((resolve, reject) => {
      if (!globalThis.indexedDB) { reject(new Error('This browser has no IndexedDB storage.')); return; }
      const r = indexedDB.open(DB, 1);
      r.onupgradeneeded = () => r.result.createObjectStore(STORE);
      r.onsuccess = () => { r.result.onversionchange = () => r.result.close(); resolve(r.result); };
      r.onerror = () => reject(r.error);
      r.onblocked = () => reject(new Error('Recovery storage is blocked by another window.'));
    });
  }
  async function entries() {
    const db = await open();
    try {
      return await new Promise((resolve, reject) => {
        const t = db.transaction(STORE, 'readonly'), s = t.objectStore(STORE);
        const keys = s.getAllKeys(), values = s.getAll();
        t.oncomplete = () => resolve(keys.result.map((k, i) => [String(k), values.result[i]]));
        t.onerror = () => reject(t.error);
      });
    } finally { db.close(); }
  }
  async function heldAreas() {
    if (!navigator.locks?.query) return null;
    const {held = []} = await navigator.locks.query();
    return new Set(held.map(l => l.name).filter(n => n.startsWith(LOCK_PREFIX)).map(n => n.slice(LOCK_PREFIX.length)));
  }
  const decoder = new TextDecoder();
  function describe(list) {
    // Each document copy is <area>/<file>.vectorcraft plus <area>/<file>.json (title, saved time).
    const areas = new Map();
    let bytes = 0;
    for (const [key, value] of list) {
      bytes += value?.byteLength || 0;
      const slash = key.indexOf('/');
      if (slash < 0) continue;
      const area = key.slice(0, slash), name = key.slice(slash + 1);
      if (!areas.has(area)) areas.set(area, []);
      if (name.endsWith('.json')) {
        try {
          const meta = JSON.parse(decoder.decode(value));
          areas.get(area).push({title: meta.title || name, saved: Number(meta.saved) || 0});
        } catch { /* not a copy's details */ }
      }
    }
    return {areas, bytes};
  }
  const size = n => n > 1048576 ? (n / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(n / 1024)) + ' KB';
  const time = s => new Date(s * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
  let orphans = [];

  async function refresh() {
    try {
      const [list, held] = await Promise.all([entries(), heldAreas()]);
      const {areas, bytes} = describe(list);
      const running = [], left = [];
      for (const [area, docs] of areas) {
        // Without Web Locks we can't tell: treat every area as still running (never offer to delete).
        (held === null || held.has(area) ? running : left).push(...docs.map(d => ({...d, area})));
      }
      orphans = [...areas.keys()].filter(area => held !== null && !held.has(area));
      const latest = Math.max(0, ...running.map(d => d.saved));
      if (!box.checked) {
        status.textContent = 'Recovery is off: no new recovery copies are saved. Tick the box to turn it back on.';
      } else if (running.length) {
        status.textContent = `Recovery ready — saves changed documents about every minute. ${running.length} open document${running.length === 1 ? '' : 's'} protected, last copy at ${time(latest)}.`;
      } else {
        status.textContent = 'Recovery ready — saves changed documents about every minute. No snapshot saved in this session yet.';
      }
      available.replaceChildren();
      if (left.length) {
        const p = document.createElement('p');
        p.textContent = `Copies left by a closed or crashed editor: ${left.map(d => `${d.title} (${time(d.saved)})`).join(', ')}.`;
        available.append(p);
      }
      reload.hidden = !left.length;
      clear.disabled = !orphans.length;
      clear.title = orphans.length ? '' : 'No old copies to clear. Copies of documents open now are kept.';
      if (bytes) {
        const p = document.createElement('p');
        p.textContent = `Recovery storage used: ${size(bytes)}.`;
        available.append(p);
      }
    } catch (error) {
      status.textContent = 'Recovery unavailable: ' + (error.message || error) + ' Save (download) your work regularly.';
    }
  }

  reload.addEventListener('click', () => {
    if (!window.confirm('Reload the editor to see its Recover Documents list? Changes made since the last recovery copy (up to a minute) are lost, so save first if you can.')) return;
    frame.contentWindow.location.reload();
    setTimeout(refresh, 5000);
  });
  clear.addEventListener('click', async () => {
    if (!orphans.length) return;
    if (!window.confirm('Delete recovery copies left by closed or crashed editors? Copies of documents open now are kept. This cannot be undone.')) return;
    try {
      const db = await open();
      const all = await entries();
      await new Promise((resolve, reject) => {
        const t = db.transaction(STORE, 'readwrite'), s = t.objectStore(STORE);
        for (const [key] of all) if (orphans.includes(key.split('/')[0])) s.delete(key);
        t.oncomplete = resolve; t.onerror = () => reject(t.error);
      });
      db.close();
    } catch (error) { status.textContent = 'Could not clear copies: ' + (error.message || error); }
    refresh();
  });
  keep.addEventListener('click', async () => {
    try {
      const granted = await navigator.storage?.persist?.();
      keep.textContent = granted ? 'Browser storage protected' : 'Protect browser storage';
      if (!granted) status.textContent = 'The browser did not protect storage (it decides by site use). Copies are still saved, but cleanup could remove them.';
    } catch { status.textContent = 'This browser cannot protect storage. Copies are still saved.'; }
  });
  navigator.storage?.persisted?.().then(p => { if (p) keep.textContent = 'Browser storage protected'; }).catch(() => {});

  panel.addEventListener('toggle', () => { if (panel.open) refresh(); });
  setInterval(() => { if (panel.open) refresh(); }, 15000);
  refresh();
})();
