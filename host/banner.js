(() => {
  const toolbar = document.getElementById('host-toolbar');
  const show = document.getElementById('show-toolbar');
  const hide = document.getElementById('hide-toolbar');
  const key = 'vectorcraft.toolbar-hidden';
  const setHidden = (hidden) => {
    if (hidden) toolbar.querySelectorAll('details').forEach(panel => { panel.open = false; });
    toolbar.hidden = hidden;
    show.hidden = !hidden;
    show.setAttribute('aria-expanded', String(!hidden));
    hide.setAttribute('aria-expanded', String(!hidden));
  };
  try { setHidden(localStorage.getItem(key) === 'true'); } catch { setHidden(false); }
  hide.addEventListener('click', () => {
    setHidden(true);
    try { localStorage.setItem(key, 'true'); } catch { /* Session-only preference. */ }
    show.focus();
  });
  show.addEventListener('click', () => {
    setHidden(false);
    try { localStorage.setItem(key, 'false'); } catch { /* Session-only preference. */ }
    hide.focus();
  });
})();
