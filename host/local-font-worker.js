/* No caching, uploads or stored font data. Route only the optional local font URLs. */
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('message', event => {
  if (event.data?.type === 'vectorcraft-font-owner' && event.ports[0]) {
    event.ports[0].postMessage({ownerId: event.source.id});
  }
});
const base = new URL('./', self.registration.scope);
const clean = value => typeof value === 'string' && value.length > 0 && !/[|\r\n\x00-\x1f]/.test(value);

async function requestOwner(clientId, action, name) {
  const client = await self.clients.get(clientId);
  if (!client) throw new Error('Editor closed');
  const ownerId = new URL(client.url).searchParams.get('local_fonts');
  const owner = ownerId && await self.clients.get(ownerId);
  const scope = new URL(self.registration.scope);
  if (!owner || new URL(owner.url).origin !== scope.origin ||
      ![scope.pathname, scope.pathname + 'index.html'].includes(new URL(owner.url).pathname)) {
    throw new Error('No local font session');
  }
  return new Promise((resolve, reject) => {
    const channel = new MessageChannel();
    const timer = setTimeout(() => { channel.port1.close(); reject(new Error('Local font session timed out')); }, 15000);
    channel.port1.onmessage = event => {
      clearTimeout(timer); channel.port1.close();
      event.data.error ? reject(new Error(event.data.error)) : resolve(event.data);
    };
    owner.postMessage({type: 'vectorcraft-local-font', action, name}, [channel.port2]);
  });
}

async function manifest(event) {
  const hosted = await fetch(event.request);
  try {
    const {rows} = await requestOwner(event.clientId, 'manifest');
    const valid = rows.filter(row => clean(row.family) && clean(row.style) && clean(row.postscriptName));
    if (!valid.length) return hosted;
    const overrides = new Set(valid.map(row => row.family + '|' + row.style));
    const text = (await hosted.text()).split('\n').filter(line => {
      const fields = line.split('|').map(field => field.trim());
      return !overrides.has(fields[0] + '|' + fields[1]);
    }).join('\n');
    const local = valid.map(row => `${row.family} | ${row.style} | fonts/__local/${encodeURIComponent(row.postscriptName)}.${row.format === 'otf' ? 'otf' : 'ttf'}`).join('\n');
    return new Response(text + '\n' + local + '\n', {
      headers: {'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store'},
    });
  } catch { return hosted; }
}

async function fontBytes(event, url) {
  try {
    const encoded = url.pathname.split('/fonts/__local/')[1] || '';
    if (!/\.(ttf|otf)$/.test(encoded) || encoded.includes('/')) throw new Error('Invalid local font URL');
    const name = decodeURIComponent(encoded.slice(0, -4));
    const {bytes} = await requestOwner(event.clientId, 'bytes', name);
    if (!(bytes instanceof ArrayBuffer)) throw new Error('Missing font bytes');
    return new Response(bytes, {headers: {'Content-Type': encoded.endsWith('.otf') ? 'font/otf' : 'font/ttf', 'Cache-Control': 'no-store'}});
  } catch {
    return new Response('Local font unavailable. Load font files again or re-enable PC fonts.', {status: 404});
  }
}
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.origin !== base.origin || event.request.method !== 'GET') return;
  const relative = url.pathname.slice(base.pathname.length);
  if (!url.pathname.startsWith(base.pathname)) return;
  if (/^vectorcraft\/fonts\/manifest\.txt$/.test(relative)) event.respondWith(manifest(event));
  else if (/^vectorcraft\/fonts\/__local\//.test(relative)) event.respondWith(fontBytes(event, url));
});
