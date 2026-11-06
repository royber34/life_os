(() => {
  const T = window.tt;
  const { CFG, mk } = T;
  const peopleCfg = CFG.people || [];
  const namedPeople = peopleCfg.filter((x) => x.group === 'founder' || x.group === 'core').map((x) => x.name);

  const pass = (r, p, v) => {
    if (!(p.lanes || []).includes(r.lane)) return false;
    if (!T.basisOk(r, v) || !T.confOk(r, v)) return false;
    if (p.person && r.person !== p.person) return false;
    return T.textOk(v.q, r.title, r.detail, r.person, r.tags || '', r.source, r.lane_label || '');
  };
  const inView = (p) => {
    const v = T.view('t', p);
    const [d0, d1] = T.domain(v);
    return dash.rows('events').filter((r) => pass(r, p, v) && T.inRange(r, d0, d1));
  };
  window.tt.timelineRows = inView;

  dash.draw('person', (sel) => {
    const people = Array.from(new Set(dash.rows('events').map((r) => r.person).filter(Boolean)));
    const core = namedPeople.filter((n) => people.includes(n));
    const rest = people.filter((n) => !namedPeople.includes(n)).sort((a, b) => a.localeCompare(b));
    sel.replaceChildren(new Option('Everyone', ''), ...core.map((n) => new Option(n, n)), ...rest.map((n) => new Option(n, n)));
    sel.value = dash.params().person || '';
    sel.onchange = () => dash.setParams({ person: sel.value || '' });
  });

  dash.draw('swim', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const v = T.view('t', p);
    const events = dash.rows('events');
    const [d0, d1] = T.domain(v);
    const rows = inView(p);
    const W = Math.max(el.clientWidth, 640);
    const labelW = W < 760 ? 120 : 168;
    const x = d3.scaleUtc([d0, d1], [labelW + 10, W - 16]);
    const [xl, xr] = x.range();
    const on = new Set(p.lanes);
    const groups = [];
    for (const lane of T.LANES) {
      if (!on.has(lane.id)) continue;
      if (!events.some((r) => r.lane === lane.id && r.kind !== 'metric')) continue; // nothing to plot here even with no filters on
      const items = rows.filter((r) => r.lane === lane.id);
      const distinct = new Set(events.filter((r) => r.lane === lane.id && r.person).map((r) => r.person));
      if (lane.family === 'people' && distinct.size >= 2) {
        groups.push({ label: lane.label, lane: lane.id, head: true, items: [] });
        const taken = (r) => namedPeople.includes(r.person);
        const subs = [
          ...namedPeople.map((n) => ({ label: n, test: (r) => r.person === n })),
          { label: 'AI coding agents', test: (r) => !taken(r) && r.person_group === 'ai' },
          { label: 'Vendors and community', test: (r) => !taken(r) && r.person_group === 'community' },
          { label: 'Other people', test: (r) => r.person && !taken(r) && r.person_group !== 'ai' && r.person_group !== 'community' },
          { label: `${lane.label}, general`, test: (r) => !r.person },
        ];
        for (const s of subs) { const it = items.filter(s.test); if (it.length) groups.push({ label: s.label, lane: lane.id, sub: true, items: it }); }
      } else groups.push({ label: lane.label, lane: lane.id, items });
    }
    const TRACK = 11;
    for (const g of groups) {
      const placed = g.items.map((r) => {
        const [a, b] = T.span(r);
        const xa = Math.max(x(a), xl);
        const xb = r.kind === 'span' ? Math.min(Math.max(x(b), xa + 5), xr) : null;
        return { r, xa, xb };
      }).sort((m, n) => m.xa - n.xa);
      const ends = [];
      for (const m of placed) {
        let t = ends.findIndex((e) => e < m.xa - 7);
        if (t < 0) { if (ends.length < 7) { t = ends.length; ends.push(0); } else t = ends.indexOf(Math.min(...ends)); }
        m.t = t;
        ends[t] = Math.max(m.xb ?? m.xa, m.xa) + 5;
      }
      g.placed = placed;
      g.h = g.head ? 20 : Math.max(26, 12 + Math.max(1, ends.length) * TRACK);
    }
    const top = 46;
    let y = top;
    for (const g of groups) { g.y = y; y += g.h; }
    const H = y + 10;
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).style('min-width', '640px').attr('role', 'img').attr('aria-label', `Chronology of ${T.META.name} by lane`);
    const phases = events.filter((r) => r.lane === 'pivot' && r.kind === 'span' && /^Phase /.test(r.title) && T.inRange(r, d0, d1)).sort(T.byDate);
    phases.forEach((r, i) => {
      const [a, b] = T.span(r);
      const xa = Math.max(x(a), xl), xb = Math.min(x(b), xr);
      if (xb - xa < 2) return;
      svg.append('rect').attr('class', 'tt-phase').attr('x', xa).attr('y', 4).attr('width', xb - xa).attr('height', H - 4).style('fill', 'var(--cds-chart-grid)').style('opacity', i % 2 ? 0.55 : 0.25);
      if (xb - xa > 46) { const t = svg.append('text').attr('x', xa + 4).attr('y', 15).style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text(r.title.split(':')[0]); T.fit(t.node(), xb - xa - 8); }
    });
    groups.forEach((g, i) => {
      if (!g.head && i % 2 === 0) svg.append('rect').attr('x', 0).attr('y', g.y).attr('width', W).attr('height', g.h).style('fill', 'var(--color-fg)').style('opacity', 0.025);
      svg.append('line').attr('x1', 0).attr('x2', W).attr('y1', g.y).attr('y2', g.y).style('stroke', 'var(--cds-chart-grid)');
      const t = svg.append('text').attr('x', g.sub ? 14 : 4).attr('y', g.y + (g.head ? 14 : Math.min(g.h / 2 + 4, 18)))
        .style('fill', g.sub ? 'var(--color-fg-muted)' : 'var(--color-fg)').style('font-size', g.sub ? '11px' : '12px').style('font-weight', g.sub ? '400' : '500').text(g.label);
      T.fit(t.node(), labelW - (g.sub ? 14 : 4));
    });
    const ax = svg.append('g').attr('transform', `translate(0,${top - 6})`).call(d3.axisTop(x).ticks(Math.max(3, Math.floor((xr - xl) / 90))).tickSizeOuter(0).tickFormat(T.monthTick));
    T.styleAxis(ax).select('.domain').remove();
    const cut = T.d(T.CUTOFF);
    if (cut >= d0 && cut <= d1) svg.append('line').attr('x1', x(cut)).attr('x2', x(cut)).attr('y1', top).attr('y2', H).style('stroke', 'var(--cds-chart-reference)').style('stroke-dasharray', '3 3');
    const selRow = p.sel ? events.find((r) => r.id === p.sel) : null;
    if (selRow && T.inRange(selRow, d0, d1)) { const sx = Math.max(x(T.d(selRow.date)), xl); svg.append('line').attr('x1', sx).attr('x2', sx).attr('y1', top).attr('y2', H).style('stroke', 'var(--color-fg)').style('opacity', 0.35); }
    const tip = T.tip(el);
    const lines = (r) => [
      ['tt-tip-date', T.fmtDate(T.d(r.date)) + (r.kind === 'span' ? ' to ' + (r.date_end ? T.fmtDate(T.d(r.date_end)) : 'now') : '')],
      ['tt-tip-title', r.title],
      ['tt-tip-meta', `${r.lane_label}${r.person ? ' · ' + r.person : ''} · ${r.basis === 'fact' ? 'Fact' : 'Inference'}, ${r.confidence} confidence`],
    ];
    const marks = svg.append('g');
    for (const g of groups) {
      for (const m of g.placed || []) {
        const r = m.r, c = T.color(r.lane), cy = g.y + 8 + m.t * TRACK + 5, isSel = r.id === p.sel;
        let node;
        if (r.kind === 'span') node = marks.append('rect').attr('x', m.xa).attr('y', cy - 3).attr('width', Math.max(5, m.xb - m.xa)).attr('height', 6).attr('rx', 3);
        else if (T.isTurning(r)) node = marks.append('path').attr('d', d3.symbol(d3.symbolDiamond, isSel ? 120 : 70)()).attr('transform', `translate(${m.xa},${cy})`);
        else node = marks.append('circle').attr('cx', m.xa).attr('cy', cy).attr('r', isSel ? 6 : 4.5);
        node.attr('class', 'tt-mark').attr('tabindex', 0).attr('role', 'button').attr('aria-label', r.title);
        if (r.basis === 'fact') node.style('fill', c).style('stroke', isSel ? 'var(--color-fg)' : 'none').style('stroke-width', 2);
        else node.style('fill', 'var(--color-panel)').style('stroke', isSel ? 'var(--color-fg)' : c).style('stroke-width', 1.6);
        if (r.confidence === 'low') node.style('opacity', 0.45); else if (r.confidence === 'medium') node.style('opacity', 0.8);
        node.on('pointerenter', (ev) => tip.show(ev, lines(r))).on('pointermove', (ev) => tip.show(ev, lines(r))).on('pointerleave', tip.hide)
          .on('click', () => dash.setParams({ sel: r.id }))
          .on('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); dash.setParams({ sel: r.id }); } });
      }
    }
    if (!groups.length) svg.append('text').attr('x', labelW + 10).attr('y', top + 20).style('fill', 'var(--color-fg-muted)').style('font-size', '12px').text('No lanes selected. Pick lanes in the filters above.');
  });

  dash.draw('swimlegend', (ul) => {
    ul.replaceChildren();
    const fams = new Set(T.LANES.map((l) => l.family));
    const add = (sw, text) => { const li = mk('li'); li.append(sw, document.createTextNode(text)); ul.append(li); };
    for (const fam of Object.keys(T.FAMLABEL)) if (fams.has(fam)) add(T.chipSwatch(T.famColor(fam), fam === 'turning_point' ? 'is-diamond' : ''), T.FAMLABEL[fam]);
    add(mk('i', 'tt-sw is-hollow'), 'Inference');
    add(T.chipSwatch(dash.colors[0], 'is-faded'), 'Low confidence');
    add(T.chipSwatch(dash.colors[0], 'is-bar'), 'Period');
  });

  dash.draw('zoomstrip', (el) => {
    el.replaceChildren();
    const src = dash.rows(el.dataset.source);
    const prefix = el.dataset.scope;
    const p = dash.params();
    const v = T.view(prefix, p);
    const W = Math.max(el.clientWidth, 280), H = 44;
    const full = T.periodRange(v.period);
    const xo = d3.scaleUtc(full, [8, W - 8]);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('aria-label', 'Zoom strip');
    svg.append('rect').attr('x', 8).attr('y', 2).attr('width', W - 16).attr('height', 24).attr('rx', 3).style('fill', 'var(--cds-chart-grid)').style('opacity', 0.4);
    for (const r of src) {
      const t = T.d(r.date);
      if (!t || t < full[0] || t > full[1]) continue;
      svg.append('line').attr('x1', xo(t)).attr('x2', xo(t)).attr('y1', 6).attr('y2', 22).style('stroke', r.lane ? T.color(r.lane) : dash.colors[0]).style('opacity', 0.5);
    }
    const ax = svg.append('g').attr('transform', 'translate(0,28)').call(d3.axisBottom(xo).ticks(Math.max(3, Math.floor(W / 110))).tickSize(3).tickFormat(T.monthTick));
    T.styleAxis(ax, '10px').select('.domain').remove();
    const brush = d3.brushX().extent([[8, 2], [W - 8, 26]]).on('end', (ev) => {
      if (!ev.sourceEvent) return;
      if (!ev.selection) { dash.setParams({ [`${prefix}from`]: null, [`${prefix}to`]: null }); return; }
      const [a, b] = ev.selection.map(xo.invert);
      if (b - a < 3 * 864e5) return;
      dash.setParams({ [`${prefix}from`]: T.iso(a), [`${prefix}to`]: T.iso(b) });
    });
    const bg = svg.append('g').call(brush);
    bg.selectAll('.selection').style('fill', 'var(--color-fg)').style('fill-opacity', 0.08).style('stroke', 'var(--color-fg-muted)');
    if (v.from && v.to) bg.call(brush.move, [xo(T.d(v.from)), xo(T.d(v.to))]);
  });

  dash.draw('detail', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const r = p.sel ? dash.rows('events').find((x) => x.id === p.sel) : null;
    if (!r) return;
    const when = T.fmtDate(T.d(r.date)) + (r.kind === 'span' ? ' to ' + (r.date_end ? T.fmtDate(T.d(r.date_end)) : 'now') : '');
    const seq = inView(p).sort(T.byDate);
    el.append(
      mk('h3', null, r.title),
      mk('div', 'tt-dmeta', [when, r.lane_label, r.person, r.function].filter(Boolean).join(' · ')),
      mk('p', 'tt-dtext', r.detail || ''),
      T.dl([
        ['Basis', r.basis === 'fact' ? 'Fact, from a cited source' : 'Inference, reasoned from the evidence cited'],
        ['Confidence', r.confidence],
        ['Source', T.links(r.source)],
        ['Tags', r.tags && r.tags.length ? r.tags : null],
        ['Record', r.id],
      ]),
      T.navButtons(seq, r.id, 'sel', 'in view'),
    );
  });

  window.tt.buildMetricCards = (host) => {
    for (const c of CFG.metric_cards || []) {
      const card = mk('div', 'tt-mcard');
      card.dataset.mcard = c.id;
      card.append(mk('h3', null, c.title));
      if (c.note) card.append(mk('p', 'tt-note', c.note));
      if (c.kind !== 'range' && (c.series || []).length > 1) {
        const ul = mk('ul', 'tt-legend');
        c.series.forEach((s, i) => { const li = mk('li'); li.append(T.chipSwatch(dash.colors[i % dash.colors.length]), document.createTextNode(s.label || s.person || s.metric)); ul.append(li); });
        card.append(ul);
      }
      const m = mk('div', 'tt-metric');
      m.dataset.draw = 'metric';
      m.dataset.card = c.id;
      card.append(m);
      host.append(card);
    }
  };

  // A sparse series reads better with a fixed bar width than with one-day bars.
  const isSparse = (rows) => {
    const dates = Array.from(new Set(rows.map((r) => r.date))).sort();
    if (dates.length < 2) return true;
    const gaps = d3.pairs(dates).map(([a, b]) => (T.d(b) - T.d(a)) / 864e5);
    return rows.length > dates.length || d3.median(gaps) > 2;
  };

  window.tt.drawSeries = (el, cfg, series, labels, ruleDates, selDate, v) => {
    const [d0, d1] = T.domain(v);
    series = series.map((s) => s.filter((r) => { const t = T.d(r.date); return t && t >= d0 && t <= d1; }).sort((a, b) => (a.date < b.date ? -1 : 1)));
    const pts = series.flat();
    if (!pts.length) { el.append(mk('div', 'tt-empty', 'No data points in this time range with the current filters.')); return; }
    const W = Math.max(el.clientWidth, 260), H = cfg.height || 150;
    const usd = pts.every((r) => r.metric_unit === 'usd');
    const fmt = (x) => (usd ? '$' : '') + T.compact(x);
    let lines = series;
    if (cfg.kind === 'line') lines = series.map((s) => Array.from(d3.rollup(s, (vs) => vs.reduce((m, r) => (Number(r.metric_value) > Number(m.metric_value) ? r : m)), (r) => r.date).values()).sort((a, b) => (a.date < b.date ? -1 : 1)));
    const norm = cfg.normalize ? lines.map((s) => d3.max(s, (r) => Number(r.metric_value)) || 1) : null;
    const val = (r, i) => (norm ? (Number(r.metric_value) / norm[i]) * 100 : Number(r.metric_value));
    const maxV = cfg.normalize ? 100 : d3.max(pts, (r) => Number(r.metric_value)) || 1;
    const yv = d3.scaleLinear([0, maxV * 1.08], [H - 22, 8]).nice();
    const yfmt = cfg.normalize ? (t) => t + '%' : fmt;
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`);
    const yt = yv.ticks(3);
    const probe = svg.append('g');
    const widths = yt.map((t) => probe.append('text').style('font-size', '10px').text(yfmt(t)).node().getComputedTextLength());
    probe.remove();
    const ml = Math.ceil(d3.max(widths) || 20) + 8;
    const mr = cfg.kind === 'line' || cfg.kind === 'range' ? 52 : 10;
    const x = d3.scaleUtc([d0, d1], [ml, W - mr]);
    for (const t of yt) {
      svg.append('line').attr('x1', ml).attr('x2', W - mr).attr('y1', yv(t)).attr('y2', yv(t)).style('stroke', 'var(--cds-chart-grid)');
      svg.append('text').attr('x', ml - 6).attr('y', yv(t) + 3).attr('text-anchor', 'end').style('fill', 'var(--color-fg-muted)').style('font-size', '10px').text(yfmt(t));
    }
    const ax = svg.append('g').attr('transform', `translate(0,${H - 20})`).call(d3.axisBottom(x).ticks(Math.max(2, Math.floor((W - ml - mr) / 80))).tickSize(3).tickFormat(T.monthTick));
    T.styleAxis(ax, '10px').select('.domain').style('stroke', 'var(--cds-chart-axis)');
    for (const t of ruleDates || []) if (t >= d0 && t <= d1) svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', 6).attr('y2', H - 22).style('stroke', 'var(--cds-chart-reference)').style('stroke-dasharray', '3 3');
    if (selDate && selDate >= d0 && selDate <= d1) svg.append('line').attr('x1', x(selDate)).attr('x2', x(selDate)).attr('y1', 6).attr('y2', H - 22).style('stroke', 'var(--color-fg)').style('opacity', 0.45);
    const col = (i) => dash.colors[i % dash.colors.length];
    const hits = [];
    if (cfg.kind === 'bar') {
      const day = 864e5;
      const bars = series.flat();
      const wide = isSparse(bars);
      for (const r of bars) {
        const t = T.d(r.date);
        const w = wide ? 7 : Math.max(1.5, x(new Date(+t + day)) - x(t) - 1);
        const val0 = Number(r.metric_value);
        svg.append('rect').attr('x', x(t) - (wide ? w / 2 : 0)).attr('y', yv(val0)).attr('width', w).attr('height', Math.max(0.5, yv(0) - yv(val0))).attr('rx', Math.min(2, w / 2)).style('fill', col(0));
        hits.push({ x: x(t), r, i: 0 });
      }
    } else if (cfg.kind === 'range') {
      const lowName = series[0][0] ? series[0][0].metric_name : null;
      for (const [date, rs] of d3.group(pts, (r) => r.date)) {
        const lo = rs.find((r) => r.metric_name === lowName), hi = rs.find((r) => r.metric_name !== lowName);
        if (!lo || !hi) continue;
        const xv = x(T.d(date));
        svg.append('rect').attr('x', xv - 6).attr('y', yv(+hi.metric_value)).attr('width', 12).attr('height', Math.max(2, yv(+lo.metric_value) - yv(+hi.metric_value))).attr('rx', 2).style('fill', col(0)).style('fill-opacity', 0.3).style('stroke', col(0));
        svg.append('text').attr('x', xv + 9).attr('y', yv(+hi.metric_value) + 4).style('fill', 'var(--color-fg-muted)').style('font-size', '10px').text(fmt(+lo.metric_value) + '–' + fmt(+hi.metric_value));
        hits.push({ x: xv, r: hi, i: 0, lo });
      }
    } else {
      const ends = [];
      lines.forEach((s, i) => {
        if (!s.length) return;
        const line = d3.line().x((r) => x(T.d(r.date))).y((r) => yv(val(r, i)));
        svg.append('path').attr('d', line(s)).style('fill', 'none').style('stroke', col(i)).style('stroke-width', 2).style('stroke-linecap', 'round').style('stroke-linejoin', 'round');
        if (s.length <= 40) for (const r of s) svg.append('circle').attr('cx', x(T.d(r.date))).attr('cy', yv(val(r, i))).attr('r', 2.5).style('fill', col(i));
        for (const r of s) hits.push({ x: x(T.d(r.date)), r, i });
        const last = s[s.length - 1];
        ends.push({ y: yv(val(last, i)), x: x(T.d(last.date)), v: Number(last.metric_value), i });
      });
      ends.sort((a, b) => a.y - b.y);
      for (let k = 1; k < ends.length; k++) if (ends[k].y - ends[k - 1].y < 11) ends[k].y = ends[k - 1].y + 11;
      for (const e of ends) svg.append('text').attr('x', Math.min(e.x + 6, W - mr + 6)).attr('y', e.y + 3).style('fill', col(e.i)).style('font-size', '10px').style('font-weight', '500').text(fmt(e.v));
    }
    const tip = T.tip(el);
    svg.append('rect').attr('x', ml).attr('y', 0).attr('width', W - mr - ml).attr('height', H - 20).style('fill', 'transparent')
      .on('pointermove', (ev) => {
        const [mx] = d3.pointer(ev);
        let best = null;
        for (const h of hits) { const dx = Math.abs(h.x - mx); if (!best || dx < best.dx) best = { ...h, dx }; }
        if (!best || best.dx > 30) { tip.hide(); return; }
        const same = hits.filter((h) => h.r.date === best.r.date);
        const out = [['tt-tip-date', T.fmtDate(T.d(best.r.date))]];
        if (cfg.kind === 'range') out.push(['tt-tip-title', fmt(+best.lo.metric_value) + ' to ' + fmt(+best.r.metric_value)]);
        else for (const h of same) out.push(['tt-tip-title', (labels[h.i] ? labels[h.i] + ': ' : '') + d3.format(',')(Number(h.r.metric_value))]);
        if (same.length === 1) out.push(['tt-tip-meta', best.r.title + (best.r.basis === 'inference' ? ' (inference)' : '')]);
        tip.show(ev, out);
      })
      .on('pointerleave', tip.hide);
  };

  dash.draw('metric', (el) => {
    el.replaceChildren();
    const cfg = (CFG.metric_cards || []).find((c) => c.id === el.dataset.card);
    if (!cfg) { el.append(T.missing(`metric card ${el.dataset.card}`)); return; }
    const p = dash.params();
    const v = T.view('t', p);
    const ok = (r) => T.basisOk(r, v) && T.confOk(r, v);
    const metrics = dash.rows('metrics');
    const series = (cfg.series || []).map((s) => {
      if (s.person && p.person && s.person !== p.person) return [];
      return metrics.filter((r) => r.metric_name === s.metric && (!s.person || r.person === s.person) && ok(r));
    });
    const rules = dash.rows('events').filter((r) => T.isTurning(r) && ok(r)).map((r) => T.d(r.date));
    const s = p.sel ? dash.rows('events').find((r) => r.id === p.sel) : null;
    T.drawSeries(el, { kind: cfg.kind }, series, (cfg.series || []).map((x) => x.label), rules, s ? T.d(s.date) : null, v);
  });

  dash.draw('rows', (tb) => {
    tb.replaceChildren();
    const p = dash.params();
    const rows = inView(p).sort(T.byDate);
    if (p.tsort === 'desc') rows.reverse();
    for (const r of rows) {
      const tr = mk('tr');
      tr.dataset.key = r.id;
      if (r.id === p.sel) tr.className = 'is-sel';
      [r.date, r.lane_label, r.title, r.person, r.basis, r.confidence, r.source].forEach((val, i) => tr.append(mk('td', i === 3 || i === 5 || i === 6 ? 'tt-hide-narrow' : null, val || '')));
      tb.append(tr);
    }
  });

  dash.draw('count', (el) => { el.textContent = d3.format(',')(inView(dash.params()).length); });
})();
