(() => {
  const T = window.tt;
  const { B, CFG, mk } = T;
  const mdInto = (cls, text, opts) => { const n = mk('div', cls); T.md(text || '', n, opts); return n; };

  // One insight: what was found, the evidence, how strong it is, and how a team can use it.
  const insightCard = (it) => {
    const c = mk('article', 'tt-insight');
    c.append(mk('h4', null, it.title));
    c.append(mdInto('tt-prose tt-insight-ev', it.evidence));
    if (it.use) {
      const u = mk('div', 'tt-insight-use');
      u.append(mk('span', 'tt-flabel', it.use_label || 'What it suggests'), mdInto('tt-prose', it.use));
      c.append(u);
    }
    if (it.measure) {
      const u = mk('div', 'tt-insight-use');
      u.append(mk('span', 'tt-flabel', 'How a test could read'), mdInto('tt-prose', it.measure));
      c.append(u);
    }
    if (it.proof) c.append(mk('span', 'tt-tag', it.proof));
    return c;
  };
  T.insightCard = insightCard;

  const COLS = [['working', 'Working', 'is-working'], ['not', "Not working or unproven", 'is-not'], ['open', 'Opportunity', 'is-open']];

  dash.draw('gtminsights', (el) => {
    if (el.dataset.done) return;
    el.dataset.done = '1';
    const ins = ((B.prose || {}).gtm || {}).insights;
    el.hidden = !ins;
    if (!ins) return;
    const part = mk('div', 'tt-part');
    part.append(mk('span', 'tt-part-kicker', 'Marketing and sales'), mk('h2', null, ins.heading || 'What has worked, what has not, and where the openings are'));
    el.append(part);
    if (ins.summary) {
      const f = mk('details', 'tt-top-more');
      f.append(mk('summary', null, 'In a few sentences'), mdInto('tt-prose', ins.summary));
      el.append(f);
    }
    if ((ins.stats || []).length) {
      const fold = mk('details', 'tt-card tt-fold');
      fold.append(mk('summary', null, `All key numbers (${ins.stats.length})`));
      const s = mk('div', 'tt-facts');
      for (const h of ins.stats) {
        const c = mk('div', 'tt-kpi tt-fact');
        c.append(mdInto('tt-kpi-value', h.value), mdInto('tt-fact-label tt-prose', h.label));
        if (h.kind) c.append(mk('span', 'tt-tag', h.kind));
        s.append(c);
      }
      fold.append(s);
      el.append(fold);
    }
    const tableCard = (t, open) => {
      const sec = mk('details', 'tt-card tt-fieldtable');
      if (open) sec.open = true;
      sec.dataset.table = t.id;
      const sum = mk('summary');
      sum.append(mk('b', null, t.title));
      sec.append(sum);
      if (t.note) sec.append(mdInto('tt-note tt-prose', t.note));
      const wrap = mk('div', 'tt-plan-wrap');
      const tb = mk('table', 'tt-plan tt-rules');
      const hr = mk('tr');
      for (const h of t.columns) hr.append(mk('th', null, h));
      const th = mk('thead'); th.append(hr);
      const body = mk('tbody');
      for (const r of t.rows) {
        const tr = mk('tr');
        for (const cell of r) { const td = mk('td'); T.md(String(cell), td); tr.append(td); }
        body.append(tr);
      }
      tb.append(th, body);
      wrap.append(tb);
      sec.append(wrap);
      return sec;
    };
    if (ins.brief) {
      el.append(tableCard({ id: 'brief', title: ins.brief.heading, note: ins.brief.note, columns: ['Part', 'Starting point'], rows: ins.brief.rows }, true));
    }
    const nav = mk('div', 'tt-row tt-insight-nav');
    nav.append(mk('span', 'tt-flabel', 'Show'));
    const views = [['all', 'Everything'], ...COLS.map(([k, l]) => [k, l])];
    let view = 'all';
    const buttons = views.map(([k, l]) => {
      const b = mk('button', 'tt-chip', l);
      b.onclick = () => { view = k; apply(); };
      nav.append(b);
      return [k, b];
    });
    el.append(nav);
    const blocks = [];
    for (const lens of ins.lenses || []) {
      const sec = mk('section', 'tt-card tt-lens');
      sec.dataset.lens = lens.id;
      const head = mk('div', 'tt-card-head');
      head.append(mk('h3', null, lens.label));
      if (lens.intro) head.append(mdInto('tt-note tt-prose', lens.intro));
      sec.append(head);
      const grid = mk('div', 'tt-lens-grid');
      for (const [k, label, cls] of COLS) {
        const col = mk('div', `tt-lens-col ${cls}`);
        col.dataset.col = k;
        col.append(mk('span', 'tt-lens-label', label));
        const list = lens[k] || [];
        for (const it of list) col.append(insightCard(it));
        if (!list.length) col.append(mk('p', 'tt-note', 'Nothing public to report here.'));
        grid.append(col);
        blocks.push(col);
      }
      sec.append(grid);
      el.append(sec);
    }
    for (const t of ins.tables || []) el.append(tableCard(t, t.id === 'calendar'));
    const apply = () => {
      for (const [k, b] of buttons) b.setAttribute('aria-pressed', String(k === view));
      for (const col of blocks) col.hidden = view !== 'all' && col.dataset.col !== view;
      for (const g of el.querySelectorAll('.tt-lens-grid')) g.classList.toggle('is-single', view !== 'all');
    };
    apply();
  });

  // Campaign impact: a metric over time with campaigns on it, then the before and after behind each verdict.
  const IMP = B.impact;
  for (const n of document.querySelectorAll('[data-needs-impact]')) n.hidden = !IMP;
  const COLORS = { 'above noise': 'var(--cds-chart-3)', negative: 'var(--cds-chart-status-critical)', 'within noise': 'var(--cds-chart-reference)' };
  const fmtPct = (v) => (v == null ? '' : `${v > 0 ? '+' : ''}${d3.format('.1f')(v)}%`);
  const fmtNum = (v) => (v == null ? '' : d3.format(',.1f')(v));
  let viewId = null, selected = null;
  const views = () => ((CFG.impact || {}).views || []);
  const viewNow = () => views().find((v) => v.id === viewId) || views()[0];
  const seriesOf = (id) => (IMP.series || []).find((s) => s.metric === id);
  const rowsFor = (v) => (IMP.rows || []).filter((r) => r.metric === v.metric).sort((a, b) => String(a.start).localeCompare(String(b.start)));
  const redraw = () => { for (const k of ['impactchart', 'impactrows', 'impactdetail']) { const n = document.querySelector(`[data-draw="${k}"]`); if (n) drawers[k](n); } };

  const drawers = {
    impactchart(el) {
      el.replaceChildren();
      const v = viewNow();
      if (!v) return;
      const s = seriesOf(v.series);
      if (!s) return;
      const pts = s.points.map(([d, n]) => [T.d(d), +n]).filter(([d, n]) => d && Number.isFinite(n));
      const W = Math.max(el.clientWidth, 640), H = 280, m = { t: 40, r: 16, b: 24, l: 44 };
      const x = d3.scaleUtc(d3.extent(pts, (p) => p[0]), [m.l, W - m.r]);
      const y = d3.scaleLinear([0, d3.max(pts, (p) => p[1]) * 1.05], [H - m.b, m.t]);
      const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).style('min-width', '640px').attr('role', 'img').attr('aria-label', `${v.label} with campaigns marked`);
      T.styleAxis(svg.append('g').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).ticks(Math.floor(W / 110)).tickSizeOuter(0)));
      const ay = T.styleAxis(svg.append('g').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5).tickFormat(d3.format('~s')).tickSize(-(W - m.l - m.r))));
      ay.select('.domain').remove();
      ay.selectAll('line').style('stroke', 'var(--cds-chart-grid)');
      const line = d3.line().x((p) => x(p[0])).y((p) => y(p[1]));
      for (const c of v.controls || []) {
        const cs = seriesOf(c);
        if (!cs) continue;
        const cp = cs.points.map(([d, n]) => [T.d(d), +n]).filter(([d, n]) => d && Number.isFinite(n) && d >= x.domain()[0] && d <= x.domain()[1]);
        const yc = d3.scaleLinear([0, d3.max(cp, (p) => p[1]) * 1.05], [H - m.b, m.t]);
        svg.append('path').attr('d', d3.line().x((p) => x(p[0])).y((p) => yc(p[1]))(cp)).style('fill', 'none').style('stroke', 'var(--cds-chart-muted)').style('stroke-width', 1).style('opacity', 0.55);
      }
      svg.append('path').attr('d', line(pts)).style('fill', 'none').style('stroke', 'var(--cds-chart-1)').style('stroke-width', 1.8);
      const tip = T.tip(el);
      const rail = 16;
      const rows = rowsFor(v).filter((r) => { const t = T.d(r.start); return t && t >= x.domain()[0] && t <= x.domain()[1]; });
      const ends = [];
      for (const r of rows) {
        const cx = x(T.d(r.start));
        let lane = ends.findIndex((e) => e < cx - 11);
        if (lane < 0) { if (ends.length < 3) { lane = ends.length; ends.push(0); } else lane = 2; }
        ends[lane] = cx;
        const cy = rail + lane * 9;
        const isSel = selected === r.campaign_id;
        svg.append('line').attr('x1', cx).attr('x2', cx).attr('y1', cy).attr('y2', H - m.b).style('stroke', isSel ? 'var(--color-fg)' : 'var(--cds-chart-reference)').style('stroke-width', isSel ? 1.5 : 0.6).style('opacity', isSel ? 0.8 : 0.35);
        const col = COLORS[r.verdict];
        const mark = svg.append('circle').attr('cx', cx).attr('cy', cy).attr('r', isSel ? 6 : 4.5).attr('class', 'tt-impact-mark').attr('tabindex', 0).attr('role', 'button').attr('aria-label', `${r.campaign}: ${r.verdict}`);
        mark.style('fill', col || 'var(--color-panel)').style('stroke', col || 'var(--cds-chart-reference)').style('stroke-width', 1.4).style('cursor', 'pointer');
        const lines = [['tt-tip-date', `${T.fmtDate(T.d(r.start))} · ${String(r.campaign_type).replace(/_/g, ' ')}`], ['tt-tip-title', r.campaign], ['tt-tip-meta', r.verdict + (r.net_pct != null ? `: net ${fmtPct(r.net_pct)}, normal range ${fmtPct(r.noise_band_lo_pct)} to ${fmtPct(r.noise_band_pct)}` : ` (${r.verdict_reason || ''})`)]];
        mark.on('pointerenter', (e) => tip.show(e, lines)).on('pointermove', (e) => tip.show(e, lines)).on('pointerleave', tip.hide)
          .on('click', () => { selected = r.campaign_id; redraw(); })
          .on('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selected = r.campaign_id; redraw(); } });
      }
      const legend = mk('div', 'tt-row tt-mlegend');
      for (const [label, c] of [['Above normal range', COLORS['above noise']], ['Below normal range', COLORS.negative], ['Within normal range', COLORS['within noise']], ['Not measurable', null]]) {
        const sp = mk('span', 'tt-note');
        const sw = mk('i', 'tt-sw');
        sw.style.background = c || 'transparent';
        if (!c) sw.style.border = '1px solid var(--cds-chart-reference)';
        sp.append(sw, document.createTextNode(` ${label}`));
        legend.append(sp);
      }
      el.append(legend);
      if ((v.controls || []).length) el.append(mk('p', 'tt-note', 'Grey lines are rival and category controls, each on its own scale.'));
    },
    impactrows(el) {
      el.replaceChildren();
      const v = viewNow();
      if (!v) return;
      const t = mk('table', 'tt-plan tt-impact-table');
      const hr = mk('tr');
      for (const h of ['Start', 'Campaign', 'Type', 'Before', 'After', 'Net of season and rivals', 'Normal range', 'Result']) hr.append(mk('th', null, h));
      const th = mk('thead'); th.append(hr);
      const tb = mk('tbody');
      for (const r of rowsFor(v)) {
        const tr = mk('tr');
        tr.dataset.impact = r.campaign_id;
        if (selected === r.campaign_id) tr.className = 'is-sel';
        tr.style.cursor = 'pointer';
        tr.onclick = () => { selected = r.campaign_id; redraw(); };
        const res = mk('td');
        const chip = mk('span', 'tt-tag', r.verdict === 'above noise' ? 'Above range' : r.verdict === 'negative' ? 'Below range' : r.verdict === 'within noise' ? 'Within range' : 'Not measurable');
        if (COLORS[r.verdict] && r.verdict !== 'within noise') chip.style.borderColor = COLORS[r.verdict];
        res.append(chip);
        tr.append(mk('td', 'tt-plan-minor', r.start), mk('td', null, r.campaign), mk('td', 'tt-plan-minor', String(r.campaign_type).replace(/_/g, ' ')), mk('td', 'tt-plan-minor', fmtNum(r.before)), mk('td', 'tt-plan-minor', fmtNum(r.after)), mk('td', null, fmtPct(r.net_pct)), mk('td', 'tt-plan-minor', r.net_pct == null ? '' : `${fmtPct(r.noise_band_lo_pct)} to ${fmtPct(r.noise_band_pct)}`), res);
        tb.append(tr);
      }
      t.append(th, tb);
      el.append(t);
    },
    impactdetail(el) {
      el.replaceChildren();
      const v = viewNow();
      const r = v && rowsFor(v).find((x) => x.campaign_id === selected);
      if (!r) { el.append(mk('p', 'tt-note', 'Before and after, seasonal change and rival change appear here for a selected campaign.')); return; }
      el.append(mk('h3', null, r.campaign));
      el.append(T.dl([
        ['Start', `${r.start} (${r.start_precision})`],
        ['Metric', r.metric_label],
        ['Window', r.window],
        ['Before and after', r.before == null ? null : `${fmtNum(r.before)} to ${fmtNum(r.after)} (${fmtPct(r.change_pct)})`],
        ['Same weeks a year earlier', fmtPct(r.prior_year_change_pct)],
        ['Rivals and category, same weeks', fmtPct(r.control_change_pct)],
        ['Net of season and rivals', fmtPct(r.net_pct)],
        ['Normal range for this window', r.net_pct == null ? null : `${fmtPct(r.noise_band_lo_pct)} to ${fmtPct(r.noise_band_pct)}`],
        ['Result', r.verdict + (r.verdict_reason ? `: ${r.verdict_reason}` : '')],
        ['Overlaps with', (r.overlaps || []).join(', ')],
        ['Note', r.note],
      ].filter(([, val]) => val)));
    },
  };

  dash.draw('impactintro', (el) => {
    if (el.dataset.done) return;
    el.dataset.done = '1';
    const text = ((B.prose || {}).gtm || {}).impact_intro;
    if (!IMP) return;
    if (text) T.md(text, el, { listClass: 'tt-findings' });
  });
  dash.draw('impactviews', (el) => {
    el.replaceChildren();
    if (!IMP) return;
    for (const v of views()) {
      const b = mk('button', 'tt-chip', v.label);
      b.dataset.iview = v.id;
      b.setAttribute('aria-pressed', String((viewNow() || {}).id === v.id));
      b.onclick = () => { viewId = v.id; redraw(); for (const n of el.children) n.setAttribute('aria-pressed', String(n.dataset.iview === v.id)); };
      el.append(b);
    }
  });
  for (const k of Object.keys(drawers)) dash.draw(k, (el) => { if (IMP) drawers[k](el); });
  dash.draw('impacttypes', (el) => {
    if (el.dataset.done) return;
    el.dataset.done = '1';
    if (!IMP) return;
    const by = d3.group(IMP.rows, (r) => r.campaign_type);
    const t = mk('table', 'tt-plan tt-impact-types');
    const hr = mk('tr');
    for (const h of ['Campaign type', 'Metric readings tested', 'Above range', 'Below range', 'Within range', 'Not measurable']) hr.append(mk('th', null, h));
    const th = mk('thead'); th.append(hr);
    const tb = mk('tbody');
    const rows = [...by].map(([type, list]) => {
      const n = (x) => list.filter((r) => r.verdict === x).length;
      return { type, tested: list.length - n('not measurable'), above: n('above noise'), neg: n('negative'), within: n('within noise'), nm: n('not measurable') };
    }).sort((a, b) => b.tested - a.tested);
    for (const r of rows) {
      const tr = mk('tr');
      tr.append(mk('td', null, String(r.type).replace(/_/g, ' ')), ...[r.tested, r.above, r.neg, r.within, r.nm].map((x) => mk('td', 'tt-plan-minor', String(x))));
      tb.append(tr);
    }
    t.append(th, tb);
    el.append(t);
  });

  // Overview: what further data would sharpen the page.
  dash.draw('connections', (el) => {
    if (el.dataset.done) return;
    el.dataset.done = '1';
    const c = ((B.prose || {}).overview || {}).connections;
    el.hidden = !c;
    if (!c) return;
    const sec = mk('section', 'tt-card');
    const head = mk('div', 'tt-card-head');
    head.append(mk('h2', null, c.heading || 'What would make this more detailed and actionable'));
    if (c.intro) head.append(mdInto('tt-note tt-prose', c.intro));
    sec.append(head);
    const wrap = mk('div', 'tt-plan-wrap');
    const t = mk('table', 'tt-plan tt-rules tt-connections');
    const hr = mk('tr');
    for (const h of ['Connection or data', 'What it adds', 'What it would settle', 'Areas it firms up']) hr.append(mk('th', null, h));
    const th = mk('thead'); th.append(hr);
    const tb = mk('tbody');
    for (const r of c.rows || []) {
      const tr = mk('tr');
      tr.append(mk('td', 'tt-conn-name', r.tool), mk('td', 'tt-plan-minor', r.adds), mk('td', null, r.settles), mk('td', 'tt-plan-minor', r.moves || ''));
      tb.append(tr);
    }
    t.append(th, tb);
    wrap.append(t);
    sec.append(wrap);
    el.append(sec);
  });
})();
