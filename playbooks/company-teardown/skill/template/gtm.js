(() => {
  const T = window.tt;
  const { B, CFG, mk } = T;
  const channelLabel = (k) => { const c = T.CHANNELS.find((x) => x.id === k); return c ? c.label : String(k || '').replace(/_/g, ' '); };
  const pass = (r, v) => T.basisOk(r, v) && T.confOk(r, v) && T.textOk(v.q, r.title, r.hook, r.cta, r.notes, r.linked_product, r.actor, r.channel, channelLabel(r.row || r.channel), r.asset_url);
  const inView = (p) => {
    const v = T.view('g', p);
    const [d0, d1] = T.domain(v);
    const on = new Set(p.gch || []);
    return dash.rows('gtm').filter((r) => { const t = T.d(r.date); return t && t >= d0 && t <= d1 && pass(r, v) && on.has(r.row); });
  };
  window.tt.gtmRows = inView;

  dash.draw('gtmintro', (el) => {
    el.replaceChildren();
    const text = ((B.prose || {}).gtm || {}).intro;
    T.md(text || `Every recorded go-to-market action, ${d3.format(',')(dash.rows('gtm').length)} in all. Use the channels to isolate one engine, the bubbles to see reach, and the response curves to see what each launch moved.`, el);
  });
  dash.draw('gtmplaybook', (el) => {
    el.replaceChildren();
    T.md(((B.prose || {}).gtm || {}).playbook || '', el, { listClass: 'tt-findings' });
  });

  dash.draw('gtmchart', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const v = T.view('g', p);
    const all = dash.rows('gtm');
    const [d0, d1] = T.domain(v);
    const rows = inView(p);
    const W = Math.max(el.clientWidth, 640);
    const labelW = W < 760 ? 128 : 188;
    // Rows dated on the read day have an unknown start, so they sit in their own band and never pile up on one date.
    const cutoffT = T.d((B.meta || {}).cutoff);
    const isRead = (r) => cutoffT && +T.d(r.date) === +cutoffT;
    const hasRead = cutoffT && rows.some(isRead);
    const bandW = hasRead ? Math.min(150, W * 0.14) : 0;
    const x = d3.scaleUtc([d0, d1], [labelW + 12, W - 18 - bandW]);
    const maxViews = d3.max(rows, (r) => Number(r.views) || 0) || 1;
    const rad = d3.scaleSqrt([0, maxViews], [3.5, 15]);
    const on = new Set(p.gch || []);
    const groups = T.CHANNELS.filter((c) => on.has(c.id)).map((c) => ({ k: c.id, label: c.label, items: rows.filter((r) => r.row === c.id) })).filter((gr) => gr.items.length);
    for (const gr of groups) {
      let readN = 0;
      const perRow = Math.max(3, Math.floor((bandW - 12) / 13));
      const placed = gr.items.map((r) => {
        const rr = r.views ? rad(Number(r.views)) : 4.5;
        if (!isRead(r)) return { r, cx: x(T.d(r.date)), rr };
        const cx = W - 18 - bandW + 12 + (readN % perRow) * 13;
        readN += 1;
        return { r, cx, rr };
      }).sort((a, b) => a.cx - b.cx);
      const ends = [];
      for (const m of placed) {
        let t = ends.findIndex((e) => e < m.cx - m.rr - 2);
        if (t < 0) { if (ends.length < 6) { t = ends.length; ends.push(0); } else t = ends.indexOf(Math.min(...ends)); }
        m.t = t;
        ends[t] = m.cx + m.rr;
      }
      gr.placed = placed;
      const tallest = d3.max(placed, (m) => m.rr) || 5;
      gr.track = Math.max(12, Math.min(2 * tallest + 2, 30));
      gr.h = Math.max(28, 10 + Math.max(1, ends.length) * gr.track);
    }
    const top = 30;
    let y = top;
    for (const gr of groups) { gr.y = y; y += gr.h; }
    const H = y + 10;
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).style('min-width', '640px').attr('role', 'img').attr('aria-label', 'Go-to-market actions by channel');
    groups.forEach((gr, i) => {
      if (i % 2 === 0) svg.append('rect').attr('x', 0).attr('y', gr.y).attr('width', W).attr('height', gr.h).style('fill', 'var(--color-fg)').style('opacity', 0.025);
      svg.append('line').attr('x1', 0).attr('x2', W).attr('y1', gr.y).attr('y2', gr.y).style('stroke', 'var(--cds-chart-grid)');
      const t = svg.append('text').attr('x', 4).attr('y', gr.y + Math.min(gr.h / 2 + 4, 18)).style('fill', 'var(--color-fg)').style('font-size', '12px').style('font-weight', '500').text(gr.label);
      T.fit(t.node(), labelW - 4);
    });
    if (hasRead) {
      svg.append('rect').attr('x', W - 18 - bandW + 4).attr('y', top).attr('width', bandW + 14).attr('height', H - top - 6).style('fill', 'var(--color-fg)').style('opacity', 0.05);
      svg.append('text').attr('x', W - 18 - bandW + 8).attr('y', top - 12).style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text('Seen on read date');
    }
    const ax = svg.append('g').attr('transform', `translate(0,${top - 6})`).call(d3.axisTop(x).ticks(Math.max(3, Math.floor((W - labelW) / 90))).tickSizeOuter(0).tickFormat(T.monthTick));
    T.styleAxis(ax).select('.domain').remove();
    for (const r of dash.rows('events').filter(T.isTurning)) {
      const t = T.d(r.date);
      if (t >= d0 && t <= d1) svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', top).attr('y2', H).style('stroke', 'var(--cds-chart-reference)').style('stroke-dasharray', '3 3');
    }
    const sel = p.gsel ? all.find((r) => r.id === p.gsel) : null;
    if (sel) { const t = T.d(sel.date); if (t >= d0 && t <= d1) svg.append('line').attr('x1', x(t)).attr('x2', x(t)).attr('y1', top).attr('y2', H).style('stroke', 'var(--color-fg)').style('opacity', 0.35); }
    const tip = T.tip(el);
    const lines = (r) => [
      ['tt-tip-date', (isRead(r) ? 'Seen on ' : '') + T.fmtDate(T.d(r.date)) + (r.time_utc ? ' ' + r.time_utc + ' UTC' : '') + ' · ' + (r.actor || '') + ' · ' + (r.format || '')],
      ['tt-tip-title', r.title],
      ['tt-tip-meta', r.views ? d3.format(',')(r.views) + ' views' + (r.likes ? ', ' + d3.format(',')(r.likes) + ' likes' : '') : r.hook],
      ['tt-tip-meta', r.lift_metric && r.lift_before != null ? `${r.lift_metric}: ${d3.format(',')(r.lift_before)} to ${d3.format(',')(r.lift_after)} (${r.lift_window || ''})` : null],
    ];
    for (const gr of groups) {
      for (const m of gr.placed) {
        const r = m.r, c = T.channelColor(gr.k), cy = gr.y + 6 + m.t * gr.track + gr.track / 2, isSel = r.id === p.gsel;
        const node = svg.append('circle').attr('cx', m.cx).attr('cy', cy).attr('r', m.rr).attr('class', 'tt-mark').attr('tabindex', 0).attr('role', 'button').attr('aria-label', r.title);
        if (r.basis === 'fact') node.style('fill', c).style('fill-opacity', r.views ? 0.55 : 1).style('stroke', isSel ? 'var(--color-fg)' : c).style('stroke-width', isSel ? 2.5 : 1);
        else node.style('fill', 'var(--color-panel)').style('stroke', isSel ? 'var(--color-fg)' : c).style('stroke-width', 1.6);
        if (r.confidence === 'low') node.style('opacity', 0.5);
        node.on('pointerenter', (e) => tip.show(e, lines(r))).on('pointermove', (e) => tip.show(e, lines(r))).on('pointerleave', tip.hide)
          .on('click', () => dash.setParams({ gsel: r.id }))
          .on('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); dash.setParams({ gsel: r.id }); } });
      }
    }
    if (!groups.length) svg.append('text').attr('x', labelW + 12).attr('y', top + 20).style('fill', 'var(--color-fg-muted)').style('font-size', '12px').text('No actions match the channels and filters selected.');
  });

  dash.draw('gtmlift', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const curves = CFG.response_curves || [];
    const on = new Set(p.glift || []);
    if (!curves.some((c) => on.has(c.id))) { el.append(mk('div', 'tt-empty', 'Pick at least one response curve above.')); return; }
    const v = T.view('g', p);
    const metrics = dash.rows('metrics');
    const series = curves.map((c) => (on.has(c.id) ? metrics.filter((r) => r.metric_name === c.metric) : []));
    const all = dash.rows('gtm');
    const views = all.map((r) => Number(r.views) || 0).filter((n) => n > 0).sort(d3.ascending);
    const cut = views.length ? d3.quantileSorted(views, 0.9) : Infinity;
    const big = all.filter((r) => Number(r.views) >= cut && pass(r, v)).map((r) => T.d(r.date));
    const sel = p.gsel ? all.find((r) => r.id === p.gsel) : null;
    T.drawSeries(el, { kind: 'line', normalize: true, height: 170 }, series, curves.map((c) => c.label), big, sel ? T.d(sel.date) : null, v);
  });

  dash.draw('gtmdetail', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const r = p.gsel ? dash.rows('gtm').find((x) => x.id === p.gsel) : null;
    if (!r) return;
    const seq = inView(p).sort(T.byDate);
    const num = (v) => (v == null || v === '' ? null : d3.format(',')(v));
    el.append(
      mk('h3', null, r.title),
      mk('div', 'tt-dmeta', [T.fmtDate(T.d(r.date)) + (r.time_utc ? ' ' + r.time_utc + ' UTC' : ''), channelLabel(r.row || r.channel), r.actor, r.format].filter(Boolean).join(' · ')),
      mk('p', 'tt-dtext', r.hook || ''),
      T.dl([
        ['Call to action', r.cta],
        ['Promotes', r.linked_product],
        ['Asset', r.asset_url ? T.links(r.asset_url) : null],
        ['Views', num(r.views)], ['Likes', num(r.likes)], ['Reposts', num(r.reposts)], ['Replies', num(r.replies)], ['Bookmarks', num(r.bookmarks)],
        ['Metrics observed', r.metrics_observed_at],
        ['Measured response', r.lift_metric && r.lift_before != null ? `${r.lift_metric}: ${num(r.lift_before)} to ${num(r.lift_after)} (${r.lift_window || 'window not stated'})` : null],
        ['Notes', r.notes],
        ['Basis', r.basis === 'fact' ? 'Fact, from a cited source' : 'Inference'],
        ['Confidence', r.confidence],
        ['Source', T.links(r.source)],
      ]),
      T.navButtons(seq, r.id, 'gsel', 'actions in view'),
    );
  });

  dash.draw('gtmrows', (tb) => {
    tb.replaceChildren();
    const p = dash.params();
    const rows = inView(p).sort(T.byDate);
    if (p.gsort === 'desc') rows.reverse();
    for (const r of rows) {
      const tr = mk('tr');
      tr.dataset.key = r.id;
      if (r.id === p.gsel) tr.className = 'is-sel';
      [r.date, channelLabel(r.row || r.channel), r.actor, r.title, r.views == null ? '' : d3.format(',')(r.views), r.basis, r.source].forEach((v, i) => tr.append(mk('td', i === 2 || i === 6 ? 'tt-hide-narrow' : null, v == null ? '' : String(v))));
      tb.append(tr);
    }
  });

  dash.draw('gtmcount', (el) => { el.textContent = d3.format(',')(inView(dash.params()).length); });
})();
