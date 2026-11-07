(() => {
  const T = window.tt;
  const { B, mk } = T;
  const CMP = (B.prose || {}).compare;
  for (const n of document.querySelectorAll('[data-needs-compare]')) n.hidden = !CMP;
  if (!CMP) return;
  const mdInto = (cls, text) => { const n = mk('div', cls); T.md(text || '', n); return n; };
  const parse = d3.utcParse('%Y-%m');
  const brands = CMP.brands || [];
  const indicators = CMP.indicators || [];
  const color = new Map(brands.map((b, i) => [b.id, b.focus ? 'var(--cds-chart-1)' : dash.colors[(i % (dash.colors.length - 1)) + 1]]));
  const state = {
    brands: new Set(brands.filter((b) => b.on !== false).map((b) => b.id)),
    indicators: new Set(indicators.filter((x) => x.on).map((x) => x.id)),
    mode: 'actual',
    from: CMP.default_from || null,
  };
  const fmt = (v) => (Math.abs(v) >= 1000 ? d3.format('.3~s')(v).replace('G', 'B') : d3.format('.3~f')(v));

  const seriesFor = (ind) => {
    const data = (CMP.series || {})[ind.id] || {};
    return brands.filter((b) => state.brands.has(b.id) && data[b.id]).map((b) => {
      let points = data[b.id].map(([d, v]) => ({ date: parse(d), v })).filter((p) => !state.from || p.date >= parse(state.from));
      if (state.mode === 'index') {
        const first = points.find((p) => p.v > 0);
        const base = first ? first.v : null;
        points = base ? points.map((p) => ({ ...p, raw: p.v, v: (100 * p.v) / base })) : [];
      }
      const limit = (ind.step === 'year' ? 400 : 32) * 864e5;
      const broken = [];
      for (const p of points) {
        const prev = broken[broken.length - 1];
        if (prev && p.date - prev.date > limit) broken.push({ date: new Date((+prev.date + +p.date) / 2), v: null });
        broken.push(p);
      }
      return { brand: b, points: broken };
    }).filter((s) => s.points.length);
  };

  const panel = (ind, width, domain) => {
    const sec = mk('section', 'tt-cmp-panel');
    sec.dataset.indicator = ind.id;
    const head = mk('div', 'tt-cmp-head');
    head.append(mk('h3', null, ind.label));
    const remove = mk('button', 'tt-cmp-x', 'Remove');
    remove.setAttribute('aria-label', `Remove ${ind.label}`);
    remove.onclick = () => { state.indicators.delete(ind.id); render(); };
    head.append(remove);
    sec.append(head);
    if (ind.what) sec.append(mdInto('tt-note tt-prose', ind.what));
    const series = seriesFor(ind);
    if (!series.length) { sec.append(mk('p', 'tt-note', 'No data for the chosen brands.')); return sec; }
    const H = 210;
    const M = { t: 10, r: 76, b: 24, l: 44 };
    const x = d3.scaleUtc().domain(domain).range([M.l, width - M.r]);
    // Marked months stay on the chart, shaded, and are left out of the scale so they don't flatten every other line.
    const shades = (ind.shade || []).map((d) => ({ ...d, a: parse(d.from), b: parse(d.to) }));
    const inShade = (p) => shades.some((d) => p.date >= d.a && p.date <= d.b);
    const all = series.flatMap((s) => s.points.filter((p) => p.v != null && !inShade(p)).map((p) => p.v));
    const y = d3.scaleLinear().domain([0, d3.max(all) * 1.05 || 1]).nice().range([H - M.b, M.t]);
    const svg = d3.create('svg').attr('viewBox', `0 0 ${width} ${H}`).attr('role', 'img').attr('aria-label', `${ind.label} over time`).attr('class', 'tt-cmp-svg');
    const g = svg.append('g');
    g.selectAll('line.grid').data(y.ticks(4)).join('line').attr('class', 'tt-cmp-grid').attr('x1', M.l).attr('x2', width - M.r).attr('y1', (d) => y(d)).attr('y2', (d) => y(d));
    g.selectAll('text.yt').data(y.ticks(4)).join('text').attr('class', 'tt-cmp-tick').attr('x', M.l - 6).attr('y', (d) => y(d) + 4).attr('text-anchor', 'end').text((d) => fmt(d));
    // Yearly values sit at mid-year, so their year labels sit there too.
    const xt = x.ticks(width < 520 ? 4 : 10).map((d) => (ind.step === 'year' ? d3.utcMonth.offset(d, 6) : d)).filter((d) => d <= domain[1]);
    g.selectAll('text.xt').data(xt).join('text').attr('class', 'tt-cmp-tick').attr('x', (d) => x(d)).attr('y', H - 6).attr('text-anchor', 'middle').text((d) => d3.utcFormat('%Y')(d));
    for (const d of shades) {
      g.append('rect').attr('class', 'tt-cmp-shade').attr('x', x(d.a)).attr('y', M.t).attr('width', Math.max(2, x(d.b) - x(d.a))).attr('height', H - M.t - M.b);
      if (d.label) g.append('text').attr('class', 'tt-cmp-tick').attr('x', x(d.a) - 4).attr('y', M.t + 10).attr('text-anchor', 'end').text(d.label);
    }
    const clipId = `cmp-clip-${ind.id}`;
    svg.append('defs').append('clipPath').attr('id', clipId).append('rect').attr('x', M.l).attr('y', M.t).attr('width', width - M.l - M.r).attr('height', H - M.t - M.b);
    const line = d3.line().defined((p) => p.v != null).x((p) => x(p.date)).y((p) => y(p.v));
    // Lines. The target brand draws last and heavier, so it stays readable.
    for (const s of [...series].sort((a, b) => (a.brand.focus ? 1 : 0) - (b.brand.focus ? 1 : 0))) {
      g.append('path').datum(s.points).attr('class', `tt-cmp-line${s.brand.focus ? ' is-focus' : ''}`).attr('d', line).attr('stroke', color.get(s.brand.id)).attr('data-brand', s.brand.id).attr('clip-path', `url(#${clipId})`);
    }
    for (const s of series) {
      const lone = s.points.filter((p, i) => p.v != null && (s.points[i - 1] || {}).v == null && (s.points[i + 1] || {}).v == null);
      g.selectAll(null).data(lone).join('circle').attr('r', 2.5).attr('cx', (p) => x(p.date)).attr('cy', (p) => y(p.v)).attr('fill', color.get(s.brand.id)).attr('data-brand', s.brand.id);
    }
    // Direct labels at the line ends, pushed apart so they don't overlap.
    const ends = series.map((s) => ({ s, y: Math.max(M.t, y(s.points[s.points.length - 1].v)) })).sort((a, b) => a.y - b.y);
    for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + 13);
    const floor = H - M.b + 4;
    if (ends.length && ends[ends.length - 1].y > floor) {
      ends[ends.length - 1].y = floor;
      for (let i = ends.length - 2; i >= 0; i--) ends[i].y = Math.min(ends[i].y, ends[i + 1].y - 13);
    }
    for (const e of ends) {
      g.append('text').attr('class', `tt-cmp-end${e.s.brand.focus ? ' is-focus' : ''}`).attr('x', width - M.r + 6).attr('y', e.y + 4).attr('fill', color.get(e.s.brand.id)).text(e.s.brand.label);
    }
    // Crosshair with every brand's value for the month.
    const cross = g.append('line').attr('class', 'tt-cmp-cross').attr('y1', M.t).attr('y2', H - M.b).style('display', 'none');
    const wrap = mk('div', 'tt-cmp-chart');
    const tip = mk('div', 'tt-cmp-tip');
    tip.hidden = true;
    const bisect = d3.bisector((p) => p.date).center;
    const known = [...new Map(series.flatMap((s) => s.points.filter((p) => p.v != null)).map((p) => [+p.date, { date: p.date }])).values()].sort((a, b) => a.date - b.date);
    const move = (ev) => {
      const [px] = d3.pointer(ev, svg.node());
      const date = x.invert(px);
      const first = known[bisect(known, date)];
      if (!first) return;
      cross.style('display', null).attr('x1', x(first.date)).attr('x2', x(first.date));
      tip.hidden = false;
      tip.replaceChildren(mk('b', null, d3.utcFormat(ind.step === 'year' ? '%Y' : '%b %Y')(first.date)));
      const rows = series.map((s) => ({ s, p: s.points[bisect(s.points, first.date)] })).filter((r) => r.p && r.p.v != null && +r.p.date === +first.date).sort((a, b) => b.p.v - a.p.v);
      for (const r of rows) {
        const row = mk('div', 'tt-cmp-tiprow');
        const sw = mk('i');
        sw.style.background = color.get(r.s.brand.id);
        row.append(sw, mk('span', null, r.s.brand.label), mk('b', null, fmt(state.mode === 'index' ? r.p.raw : r.p.v)));
        tip.append(row);
      }
      const rect = wrap.getBoundingClientRect();
      const scale = rect.width / width;
      const left = x(first.date) * scale;
      tip.style.left = `${left > rect.width / 2 ? left - tip.offsetWidth - 10 : left + 10}px`;
    };
    svg.append('rect').attr('x', M.l).attr('y', M.t).attr('width', width - M.l - M.r).attr('height', H - M.b - M.t).attr('fill', 'transparent')
      .on('pointermove', move).on('pointerleave', () => { cross.style('display', 'none'); tip.hidden = true; });
    wrap.append(svg.node(), tip);
    sec.append(wrap);
    if (ind.note) sec.append(mdInto('tt-note tt-prose', ind.note));
    return sec;
  };

  let root = null;
  let chipsI = null;
  let chipsB = null;
  let panels = null;
  let bMode = null;
  function render() {
    if (!root) return;
    for (const b of chipsI.children) b.setAttribute('aria-pressed', String(state.indicators.has(b.dataset.id)));
    for (const b of chipsB.children) b.setAttribute('aria-pressed', String(state.brands.has(b.dataset.id)));
    for (const b of bMode.children) b.setAttribute('aria-pressed', String(b.dataset.mode === state.mode));
    panels.replaceChildren();
    const chosen = indicators.filter((x) => state.indicators.has(x.id));
    if (!chosen.length) { panels.append(mk('p', 'tt-note', 'Click an indicator above to add a chart.')); return; }
    const dates = chosen.flatMap((ind) => seriesFor(ind).flatMap((s) => s.points.map((p) => p.date)));
    if (!dates.length) { panels.append(mk('p', 'tt-note', 'Click a brand above to add it.')); return; }
    const domain = d3.extent(dates);
    const width = Math.max(320, panels.clientWidth || root.clientWidth || 900);
    for (const ind of chosen) panels.append(panel(ind, width, domain));
  }

  dash.draw('comparehead', (el) => { if (CMP.heading) el.textContent = CMP.heading; });
  dash.draw('compareintro', (el) => { el.replaceChildren(); T.md(CMP.intro || '', el); });
  dash.draw('compare', (el) => {
    if (root) { render(); return; }
    root = el;
    const toggle = (set, id) => { if (set.has(id)) set.delete(id); else set.add(id); render(); };
    const label = (t) => mk('span', 'tt-flabel', t);
    const rowI = mk('div', 'tt-row tt-cmp-row');
    chipsI = mk('div', 'tt-row');
    for (const x of indicators) { const b = mk('button', 'tt-chip', x.short || x.label); b.dataset.id = x.id; b.onclick = () => toggle(state.indicators, x.id); chipsI.append(b); }
    rowI.append(label('Charts'), chipsI);
    const rowB = mk('div', 'tt-row tt-cmp-row');
    chipsB = mk('div', 'tt-row');
    for (const b0 of brands) {
      const b = mk('button', 'tt-chip tt-cmp-brand', '');
      const sw = mk('i');
      sw.style.background = color.get(b0.id);
      b.append(sw, document.createTextNode(b0.label));
      b.dataset.id = b0.id;
      b.onclick = () => toggle(state.brands, b0.id);
      chipsB.append(b);
    }
    rowB.append(label('Brands'), chipsB);
    const rowM = mk('div', 'tt-row tt-cmp-row');
    bMode = mk('div', 'tt-row');
    for (const [id, text] of [['actual', 'Actual values'], ['index', 'Change since the start (start = 100)']]) {
      const b = mk('button', 'tt-chip', text);
      b.dataset.mode = id;
      b.onclick = () => { state.mode = id; render(); };
      bMode.append(b);
    }
    rowM.append(label('Show'), bMode);
    panels = mk('div', 'tt-cmp-panels');
    el.append(rowI, rowB, rowM, panels);
    render();
    let last = el.clientWidth;
    new ResizeObserver(() => { if (Math.abs(el.clientWidth - last) > 40) { last = el.clientWidth; render(); } }).observe(el);
  });
})();
