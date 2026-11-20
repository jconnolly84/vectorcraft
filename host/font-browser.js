(() => {
  const category = document.getElementById('font-category');
  const search = document.getElementById('font-search');
  const list = document.getElementById('font-list');
  const status = document.getElementById('font-browser-status');
  let fonts = [];
  function render() {
    const query = search.value.trim().toLowerCase();
    const shown = fonts.filter(font => (category.value === 'All categories' || font.category === category.value)
      && font.family.toLowerCase().includes(query));
    list.replaceChildren();
    for (const font of shown) {
      const row = document.createElement('li');
      const name = document.createElement('span');
      name.textContent = font.family;
      const detail = document.createElement('small');
      detail.textContent = font.category;
      name.append(detail);
      const copy = document.createElement('button');
      copy.type = 'button'; copy.textContent = 'Copy name';
      copy.setAttribute('aria-label', `Copy ${font.family} font name`);
      copy.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(font.family);
          status.textContent = `${font.family} copied. Paste into the Type tool’s font field.`;
        } catch { status.textContent = `Select and copy this name manually: ${font.family}`; }
      });
      row.append(name, copy); list.append(row);
    }
    status.textContent = `${shown.length} font families`;
  }
  category.addEventListener('change', render);
  search.addEventListener('input', render);
  fetch('./font-catalog.json').then(response => {
    if (!response.ok) throw new Error('Catalog unavailable');
    return response.json();
  }).then(data => {
    fonts = data;
    for (const name of [...new Set(fonts.map(font => font.category))].sort()) {
      const option = document.createElement('option'); option.textContent = name; category.append(option);
    }
    render();
  }).catch(() => {status.textContent = 'Font library could not load. Refresh to try again.';});
})();
