/* Load the editor in the frame, keeping renderer flags (?webgl etc.) and any fragment. */
(() => {
  const frame = document.getElementById('editor');
  if (!frame.src) frame.src = './vectorcraft/' + window.location.search + window.location.hash;
  // Closing the font panel returns keyboard focus to the editor.
  for (const panel of document.querySelectorAll('#host-toolbar details')) {
    panel.addEventListener('toggle', () => {
      if (panel.open) document.querySelectorAll('#host-toolbar details').forEach(other => { if (other !== panel) other.open = false; });
      else frame.focus();
    });
  }
})();
