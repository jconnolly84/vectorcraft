/* Local-only adapter for VectorCraft's school font manifest. */
(() => {
  const enable = document.getElementById('enable-local-fonts');
  const disable = document.getElementById('disable-local-fonts');
  const status = document.getElementById('local-font-status');
  const frame = document.getElementById('editor');
  const choose = document.getElementById('choose-font-files');
  const input = document.getElementById('font-files');
  const apply = document.getElementById('apply-font-files');
  const fileStatus = document.getElementById('font-file-status');
  const cancelFiles = document.getElementById('cancel-font-files');
  let pcFonts = new Map(), fileFonts = new Map(), pendingFiles = new Map();
  function fonts() {
    const faces = new Map([...pcFonts.values(), ...fileFonts.values()].map(font => [font.family + '|' + font.style, font]));
    return new Map([...faces.values()].map(font => [font.postscriptName, font]));
  }
  let ownerId;
  const clean = value => typeof value === 'string' && value.length > 0 && !/[|\r\n\x00-\x1f]/.test(value);
  if (!('serviceWorker' in navigator)) {
    enable.disabled = choose.disabled = true;
    status.textContent = 'Local font loading needs browser service workers. The hosted library is still available.';
    return;
  }
  if (!('queryLocalFonts' in window)) {
    enable.disabled = true;
    status.textContent = 'PC font access needs desktop Chrome or Edge. You can still load .ttf and .otf files above.';
  } else status.textContent = 'Off. Your browser will ask permission when you enable this.';

  // Respond only to our own service worker. No font bytes go to network fetch().
  navigator.serviceWorker.addEventListener('message', async event => {
    const port = event.ports[0];
    if (!port || event.data?.type !== 'vectorcraft-local-font') return;
    try {
      if (event.data.action === 'manifest') {
        port.postMessage({rows: [...fonts().values()].map(font => ({
          family: font.family, style: font.style, postscriptName: font.postscriptName, format: font.format,
        }))});
      } else if (event.data.action === 'bytes') {
        const font = fonts().get(event.data.name);
        if (!font) throw new Error('Font unavailable');
        const bytes = await (await font.blob()).arrayBuffer();
        port.postMessage({bytes}, [bytes]);
      }
    } catch {
      port.postMessage({error: 'Local font access failed. Load the font files again, re-enable PC fonts, or use a hosted font.'});
    } finally { port.close(); }
  });

  function restart(id) {
    const url = new URL('./vectorcraft/', window.location.href);
    url.search = window.location.search;
    url.searchParams.delete('local_fonts');
    if (id) url.searchParams.set('local_fonts', id);
    url.hash = window.location.hash;
    frame.src = url.href;
  }
  async function connect() {
    const registration = await navigator.serviceWorker.register(new URL('./local-font-worker.js?v=__FONT_WORKER_VERSION__', window.location.href), {scope: './', updateViaCache: 'none'});
    const worker = registration.installing || registration.waiting || registration.active;
    if (worker.state !== 'activated') {
      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('Font adapter did not start. Please try again.')), 20000);
        worker.addEventListener('statechange', () => {
          if (worker.state === 'activated') { clearTimeout(timer); resolve(); }
          else if (worker.state === 'redundant') { clearTimeout(timer); reject(new Error('Font adapter could not start.')); }
        });
      });
    }
    return new Promise((resolve, reject) => {
      const channel = new MessageChannel();
      const timer = setTimeout(() => reject(new Error('Font adapter did not respond.')), 10000);
      channel.port1.onmessage = event => {
        clearTimeout(timer); channel.port1.close();
        event.data.ownerId ? resolve(event.data.ownerId) : reject(new Error('Font adapter connection failed.'));
      };
      registration.active.postMessage({type: 'vectorcraft-font-owner'}, [channel.port2]);
    });
  }
  enable.addEventListener('click', async () => {
    if (!window.confirm('Save or export any open work first. Enabling PC fonts restarts the editor and discards unsaved work. Continue?')) return;
    enable.disabled = true;
    status.textContent = 'Waiting for font permission…';
    try {
      // Request directly from the user's click, before awaiting service worker setup.
      const available = await window.queryLocalFonts();
      const selected = new Map(available.filter(font =>
        clean(font.family) && clean(font.style) && clean(font.postscriptName))
        .map(font => [font.postscriptName, font]));
      if (!selected.size) throw new Error('The browser returned no usable local fonts.');
      ownerId = await connect();
      pcFonts = selected;
      restart(ownerId);
      status.textContent = `${fonts().size} local font faces available. They load on demand and remain on this PC. Re-enable after reopening this page.`;
      disable.hidden = false;
      enable.textContent = 'Refresh PC font list';
    } catch (error) {
      status.textContent = error.name === 'NotAllowedError'
        ? 'Font access was not allowed. Allow local fonts in browser site settings, or ask school IT if managed policy blocks it. Hosted fonts still work.'
        : (error.message || 'Local fonts could not be enabled. Hosted fonts still work.');
    } finally { enable.disabled = false; }
  });
  choose.addEventListener('click', () => input.click());
  input.addEventListener('change', async () => {
    const files = [...input.files];
    input.value = '';
    if (!files.length) return;
    pendingFiles = new Map(); apply.hidden = cancelFiles.hidden = true;
    if (files.length > 64) {fileStatus.textContent = 'Choose at most 64 font files at a time.'; return;}
    choose.disabled = true;
    fileStatus.textContent = 'Checking font files locally...';
    const failures = [];
    try {
      let total = 0;
      for (const file of files) {
        try {
          if (!/\.(ttf|otf)$/i.test(file.name) || !file.size || file.size > 32 * 1024 * 1024) throw new Error('Choose a .ttf or .otf file up to 32 MB.');
          total += file.size;
          if (total > 128 * 1024 * 1024) throw new Error('Choose fewer files (128 MB maximum).');
          const bytes = await file.arrayBuffer();
          const info = window.vectorcraftReadFontInfo(bytes);
          // Browser validation catches corrupt fonts before the editor restarts.
          await new FontFace('VectorCraftFontCheck', bytes).load();
          const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), b => b.toString(16).padStart(2, '0')).join('');
          pendingFiles.set('file-' + digest, {...info, postscriptName: 'file-' + digest, size: file.size, blob: async () => file});
        } catch (error) {failures.push(file.name + ': ' + error.message);}
      }
      const labels = [...pendingFiles.values()].map(font => font.family + ' (' + font.style + ')');
      fileStatus.textContent = (labels.length ? 'Ready: ' + labels.join(', ') + '. Save your work, then apply to restart the editor. ' : 'No usable font files. ') + failures.join(' ');
      apply.hidden = cancelFiles.hidden = !pendingFiles.size;
    } finally {choose.disabled = false;}
  });
  cancelFiles.addEventListener('click', () => {
    pendingFiles.clear(); apply.hidden = cancelFiles.hidden = true;
    fileStatus.textContent = 'Font selection cleared. The editor was not restarted.';
  });
  apply.addEventListener('click', async () => {
    if (!pendingFiles.size) return;
    apply.disabled = choose.disabled = cancelFiles.disabled = true;
    fileStatus.textContent = 'Loading the chosen fonts into this page...';
    try {
      const merged = new Map(fileFonts);
      for (const [key, font] of pendingFiles) {
        for (const [oldKey, old] of merged) if (old.family === font.family && old.style === font.style) merged.delete(oldKey);
        merged.set(key, font);
      }
      if (merged.size > 64 || [...merged.values()].reduce((sum, font) => sum + font.size, 0) > 128 * 1024 * 1024) throw new Error('The loaded-font limit is 64 faces or 128 MB. Reopen this page to start a fresh font session.');
      ownerId = ownerId || await connect();
      fileFonts = merged;
      restart(ownerId);
      fileStatus.textContent = [...fileFonts.values()].map(font => font.family + ' (' + font.style + ')').join(', ') + '. Available in the Type font list after the restart. Files stay in this page session only.';
      pendingFiles.clear(); apply.hidden = cancelFiles.hidden = true;
    } catch (error) {fileStatus.textContent = error.message || 'Font files could not be loaded.';}
    finally {apply.disabled = choose.disabled = cancelFiles.disabled = false;}
  });
  disable.addEventListener('click', () => {
    if (!window.confirm('Save or export any open work first. Disabling PC fonts restarts the editor and discards unsaved work. Continue?')) return;
    pcFonts.clear();
    restart(fileFonts.size ? ownerId : undefined);
    disable.hidden = true;
    enable.textContent = 'Use fonts from this PC';
    status.textContent = (fileFonts.size ? 'Loaded font files remain available. ' : '') + 'PC fonts off. The hosted font library is still available. You can revoke local font permission in browser site settings.';
  });
})();
