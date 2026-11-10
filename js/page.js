/* Two faces of the constituency. 2010 Westminster seats on a plain MapLibre base map (OpenFreeMap Positron), coloured by
 * how often the MP named the seat's own places per 100 Facebook posts minus per 100 spoken Commons contributions,
 * February 2017 to October 2020. Counts only; no post text. Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => Number(n).toLocaleString('en-GB');
  const DIV = ['#2F6A9E', '#C9C2B4', '#E9B49E', '#B4442E', '#6E1F12'];
  const SEQ_F = ['#FBEAE2', '#E9B49E', '#C8644A', '#8E2D1C', '#5A160B'];
  const SEQ_C = ['#E6EEF5', '#A9C4DC', '#5D8EBB', '#2F6A9E', '#173B5C'];
  let map = null, G = null, S = null, mode = 'g';
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => { ct.classList.toggle('folded', f); document.getElementById('ctToggle').setAttribute('aria-expanded', !f); };
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function colorExpr() {
    if (mode === 'f') return ['interpolate', ['linear'], ['get', 'f'], 0, SEQ_F[0], 20, SEQ_F[1], 40, SEQ_F[2], 70, SEQ_F[3], 110, SEQ_F[4]];
    if (mode === 'c') return ['interpolate', ['linear'], ['get', 'c'], 0, SEQ_C[0], 5, SEQ_C[1], 10, SEQ_C[2], 20, SEQ_C[3], 40, SEQ_C[4]];
    return ['interpolate', ['linear'], ['get', 'g'], -20, DIV[0], 0, DIV[1], 20, DIV[2], 40, DIV[3], 60, DIV[4]];
  }
  function key() {
    const t = document.getElementById('keyTitle'), b = document.getElementById('keyBar'), e = document.getElementById('keyEnds'), s = document.getElementById('keySub');
    if (mode === 'f') { t.textContent = 'Facebook'; b.style.background = `linear-gradient(90deg,${SEQ_F.join(',')})`; e.innerHTML = '<span>0</span><span>40</span><span>110+</span>'; s.textContent = 'own-seat place mentions per 100 posts'; }
    else if (mode === 'c') { t.textContent = 'House of Commons'; b.style.background = `linear-gradient(90deg,${SEQ_C.join(',')})`; e.innerHTML = '<span>0</span><span>10</span><span>40+</span>'; s.textContent = 'own-seat place mentions per 100 contributions'; }
    else { t.textContent = 'Facebook minus Commons'; b.style.background = `linear-gradient(90deg,${DIV.join(',')})`; e.innerHTML = '<span>-20</span><span>0</span><span>+60</span>'; s.textContent = 'own-seat place mentions per 100 items'; }
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
  }
  function refresh() { map.setPaintProperty('seats', 'fill-color', colorExpr()); key(); }
  function popup(seat, ll) {
    const L = S.seats[seat];
    let h = `<b class="t">${esc(seat)}</b>`;
    if (!L) {
      h += '<p class="nt">No MP for this seat has a page in the list, so there is nothing to compare.</p>';
    } else L.forEach((m, i) => {
      h += `<div class="${i ? 'pl' : ''}"><b>${esc(m.m)}</b> <span class="nt">(${esc(m.p)})</span><table>`;
      h += `<tr><td>Facebook</td><td><b>${m.f.toFixed(1)}</b> per 100 posts (${fmt(m.nf)} posts)</td></tr>`;
      h += `<tr><td>Commons</td><td><b>${m.c.toFixed(1)}</b> per 100 contributions (${fmt(m.nc)})</td></tr></table>`;
      if (!m.ok) h += '<p class="nt">Fewer than 20 items in one venue: treat with care.</p>';
      h += '<table><tr><td><b>Place</b></td><td><b>Facebook posts</b></td><td><b>Commons</b></td></tr>';
      m.pl.forEach(p => { h += `<tr><td>${esc(p[1] ? 'in ' + p[0] : p[0])}${p[4] === 'fb_top' ? ' *' : ''}</td><td>${fmt(p[2])}</td><td>${fmt(p[3])}</td></tr>`; });
      h += '</table>';
      if (m.pl.some(p => p[4] === 'fb_top')) h += '<p class="nt">* added because the MP named it most on Facebook; not in the main comparison.</p>';
      h += '</div>';
    });
    h += '<p class="nt">Counts of posts or spoken contributions naming each place, on days the MP held the seat, February 2017 to October 2020. Sources: the author\'s CrowdTangle list (counts only); Hansard (Open Parliament Licence v3.0).</p>';
    new maplibregl.Popup({ maxWidth: '340px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function centroid(f) {
    let xs = 0, ys = 0, n = 0;
    const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
    let best = null, ba = -1;
    polys.forEach(p => { const r = p[0]; let a = 0; for (let i = 1; i < r.length; i++) a += Math.abs((r[i][0] - r[i - 1][0]) * (r[i][1] + r[i - 1][1])); if (a > ba) { ba = a; best = r; } });
    best.forEach(c => { xs += c[0]; ys += c[1]; n++; });
    return [xs / n, ys / n];
  }
  function bounds(f) {
    let b = [180, 90, -180, -90];
    (f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates).forEach(p => p[0].forEach(c => { b = [Math.min(b[0], c[0]), Math.min(b[1], c[1]), Math.max(b[2], c[0]), Math.max(b[3], c[1])]; }));
    return [[b[0], b[1]], [b[2], b[3]]];
  }
  function setup() {
    G.features.forEach((f, i) => {
      const L = S.seats[f.properties.s]; f.id = i;
      if (L) { f.properties.has = 1; f.properties.g = L[0].g; f.properties.f = L[0].f; f.properties.c = L[0].c; } else f.properties.has = 0;
    });
    map.addSource('s', { type: 'geojson', data: G });
    const lbl = map.getStyle().layers.find(l => l.type === 'symbol');
    const cv = document.createElement('canvas'); cv.width = cv.height = 12; const cx = cv.getContext('2d');
    cx.fillStyle = 'rgba(255,255,255,0.75)'; cx.fillRect(0, 0, 12, 12); cx.strokeStyle = '#B9AE96'; cx.lineWidth = 1.2;
    cx.beginPath(); cx.moveTo(0, 12); cx.lineTo(12, 0); cx.moveTo(-6, 6); cx.lineTo(6, -6); cx.moveTo(6, 18); cx.lineTo(18, 6); cx.stroke();
    map.addImage('hatch', { width: 12, height: 12, data: cx.getImageData(0, 0, 12, 12).data });
    map.addLayer({ id: 'none', type: 'fill', source: 's', filter: ['==', ['get', 'has'], 0], paint: { 'fill-pattern': 'hatch' } }, lbl && lbl.id);
    map.addLayer({ id: 'seats', type: 'fill', source: 's', filter: ['==', ['get', 'has'], 1], paint: { 'fill-color': colorExpr(), 'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.95, 0.8] } }, lbl && lbl.id);
    map.addLayer({ id: 'lines', type: 'line', source: 's', paint: { 'line-color': '#8C7B5A', 'line-width': ['interpolate', ['linear'], ['zoom'], 4, 0.2, 9, 1.2], 'line-opacity': 0.8 } }, lbl && lbl.id);
    map.addLayer({ id: 'sel', type: 'line', source: 's', filter: ['==', ['get', 's'], ''], paint: { 'line-color': '#2B2119', 'line-width': 2.5 } });
    let hov = null;
    ['seats', 'none'].forEach(id => {
      map.on('click', id, e => { const f = e.features[0]; map.setFilter('sel', ['==', ['get', 's'], f.properties.s]); popup(f.properties.s, e.lngLat); });
      map.on('mousemove', id, e => { map.getCanvas().style.cursor = 'pointer'; if (hov !== null) map.setFeatureState({ source: 's', id: hov }, { hover: false }); hov = e.features[0].id; map.setFeatureState({ source: 's', id: hov }, { hover: true }); });
      map.on('mouseleave', id, () => { map.getCanvas().style.cursor = ''; if (hov !== null) map.setFeatureState({ source: 's', id: hov }, { hover: false }); hov = null; });
    });
    const tog = (box, ids) => document.getElementById(box).addEventListener('change', e => ids.forEach(id => map.setLayoutProperty(id, 'visibility', e.target.checked ? 'visible' : 'none')));
    tog('lyS', ['seats']); tog('lyN', ['none']); tog('lyO', ['lines']);
    const symbols = map.getStyle().layers.filter(l => l.type === 'symbol').map(l => l.id);
    tog('lyL', symbols);
    // search: seats, MPs and places
    const idx = [];
    G.features.forEach(f => { idx.push({ k: norm(f.properties.s), t: f.properties.s, sub: 'seat', f }); });
    Object.entries(S.seats).forEach(([seat, L]) => {
      const f = G.features.find(x => x.properties.s === seat);
      L.forEach(m => { idx.push({ k: norm(m.m), t: m.m, sub: 'MP for ' + seat, f }); m.pl.forEach(p => idx.push({ k: norm(p[0]), t: p[0], sub: 'place in ' + seat, f })); });
    });
    const q = document.getElementById('q'), sug = document.getElementById('sug');
    let hits = [], cur = -1;
    function go(h) {
      sug.style.display = 'none'; q.value = h.t; map.fitBounds(bounds(h.f), { padding: small ? 30 : 80, maxZoom: 11 });
      map.setFilter('sel', ['==', ['get', 's'], h.f.properties.s]);
      map.once('moveend', () => popup(h.f.properties.s, centroid(h.f)));
    }
    q.addEventListener('input', () => {
      const v = norm(q.value.trim()); cur = -1;
      if (v.length < 2) { sug.style.display = 'none'; return; }
      const seen = new Set();
      hits = idx.filter(x => x.k.includes(v)).sort((a, b) => (b.k.startsWith(v) - a.k.startsWith(v)) || a.k.length - b.k.length).filter(x => { const k = x.t + x.sub; if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 8);
      sug.innerHTML = hits.map((h, i) => `<li role="option" data-i="${i}">${esc(h.t)} <span>${esc(h.sub)}</span></li>`).join('') || '<li>No match</li>';
      sug.style.display = 'block';
    });
    sug.addEventListener('click', e => { const li = e.target.closest('li[data-i]'); if (li) go(hits[+li.dataset.i]); });
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); cur = Math.max(0, Math.min(hits.length - 1, cur + (e.key === 'ArrowDown' ? 1 : -1))); sug.querySelectorAll('li').forEach((l, i) => l.setAttribute('aria-selected', i === cur)); }
      if (e.key === 'Enter' && hits.length) go(hits[Math.max(cur, 0)]);
      if (e.key === 'Escape') sug.style.display = 'none';
    });
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
    key();
  }
  const lb = document.getElementById('lyrBtn'), lp = document.getElementById('lp');
  lb.addEventListener('click', () => { const o = !lp.classList.contains('open'); lp.classList.toggle('open', o); lb.setAttribute('aria-expanded', o); });
  Promise.all([fetch('data/seats_map.geojson').then(r => r.json()), fetch('data/site.json').then(r => r.json())]).then(([g, s]) => {
    G = g; S = s;
    map = new maplibregl.Map({ container: 'map', style: STYLE, bounds: [[-8.7, 49.8], [1.9, 59.4]], fitBoundsOptions: { padding: small ? 10 : 30 }, attributionControl: { compact: true }, minZoom: 3.5, maxZoom: 14 });
    window.__map = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.on('load', () => { document.getElementById('nojs').style.display = 'none'; setup(); });
  }).catch(() => { document.getElementById('nojs').textContent = 'The map data could not be loaded.'; });
})();
