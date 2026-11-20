(() => {
  const button = document.getElementById('fullscreen-toggle');
  const status = document.getElementById('fullscreen-status');
  if (!document.fullscreenEnabled) {
    button.disabled = true;
    button.title = 'Fullscreen is unavailable in this browser or blocked by policy.';
    return;
  }
  function update() {
    const active = Boolean(document.fullscreenElement);
    button.textContent = active ? 'Exit full screen' : 'Full screen';
    button.setAttribute('aria-pressed', String(active));
  }
  document.addEventListener('fullscreenchange', update);
  button.addEventListener('click', async () => {
    status.textContent = '';
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
      update();
    } catch { status.textContent = 'Fullscreen was blocked. Press F11 instead.'; }
  });
  update();
})();
