/* Load the editor in the frame, keeping renderer flags (?webgl etc.) and any fragment. */
(() => {
  const frame = document.getElementById('editor');
  if (!frame.src) frame.src = './vectorcraft/' + window.location.search + window.location.hash;
  // Closing the font panel returns keyboard focus to the editor.
  const panel = document.getElementById('font-tools');
  panel.addEventListener('toggle', () => { if (!panel.open) frame.focus(); });
})();
