// Optional tab. Drawn only when config.market is set; the validator rejects a partial block.
(() => {
  const T = window.tt;
  const { mk } = T;
  const M = T.CFG.market || { domains: [], tiers: [], fits: [] };
  const label = (list, v) => { const x = (list || []).find((i) => i.id === v); return x ? x.label : v; };
  const domLabel = (v) => label(M.domains, v);
  const tierLabel = (v) => label(M.tiers, v);
  const fitLabel = (v) => label(M.fits, v);
  const matches = (seg, row) => (seg.key_supply || []).includes(row.id);
  const segRow = (p) => (p.seg ? dash.rows('demand').find((r) => r.id === p.seg) : null);
  const pass = (r, p, opts = {}) => {
    if (!opts.ignoreDom && p.sdom && r.domain !== p.sdom) return false;
    if (!opts.ignoreTier && p.stier && r.access_tier !== p.stier) return false;
    if (p.sfit && r.fit !== p.sfit) return false;
    if (!T.confOk(r, { conf: p.sconf })) return false;
    const seg = segRow(p);
    if (seg && !matches(seg, r)) return false;
    return T.textOk(p.sq, r.name, r.provider_org, r.subcategory, r.what, r.notes);
  };
  const domIds = () => M.domains.map((d) => d.id);
  const tierIds = () => M.tiers.map((d) => d.id);
  const byPriority = () => dash.rows('demand').slice().sort((a, b) => (Number(b.priority_score) || 0) - (Number(a.priority_score) || 0));

  dash.draw('supplymatrix', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const rows = dash.rows('supply').filter((r) => pass(r, p, { ignoreDom: true, ignoreTier: true }));
    const doms = domIds().filter((d) => rows.some((r) => r.domain === d));
    const tiers = tierIds().filter((t) => rows.some((r) => r.access_tier === t));
    if (!doms.length) { el.append(mk('div', 'tt-empty', 'No sources match the current filters.')); return; }
    const W = Math.max(el.clientWidth, 560);
    const labelW = 132, top = 40, cellH = 30;
    const cw = (W - labelW - 8) / tiers.length;
    const H = top + doms.length * cellH + 6;
    const counts = d3.rollup(rows, (v) => v, (r) => r.domain, (r) => r.access_tier);
    const maxC = d3.max(doms.flatMap((d) => tiers.map((t) => (counts.get(d)?.get(t) || []).length))) || 1;
    const op = d3.scaleLinear([0, maxC], [0.06, 0.85]);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).style('min-width', '560px').attr('role', 'img').attr('aria-label', 'Sources by domain and access tier');
    tiers.forEach((t, j) => {
      const tx = svg.append('text').attr('x', labelW + j * cw + cw / 2).attr('y', top - 10).attr('text-anchor', 'middle').style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text(tierLabel(t));
      T.fit(tx.node(), cw - 4);
    });
    const tip = T.tip(el);
    doms.forEach((d, i) => {
      const yy = top + i * cellH;
      const lt = svg.append('text').attr('x', 4).attr('y', yy + cellH / 2 + 4).style('fill', 'var(--color-fg)').style('font-size', '12px').style('font-weight', p.sdom === d ? '600' : '400').text(domLabel(d));
      T.fit(lt.node(), labelW - 8);
      tiers.forEach((t, j) => {
        const list = counts.get(d)?.get(t) || [];
        const xx = labelW + j * cw;
        const isSel = p.sdom === d && p.stier === t;
        const cell = svg.append('rect').attr('class', 'tt-cell').attr('x', xx + 2).attr('y', yy + 2).attr('width', cw - 4).attr('height', cellH - 4).attr('rx', 3)
          .style('fill', list.length ? dash.colors[0] : 'var(--cds-chart-grid)').style('fill-opacity', list.length ? op(list.length) : 0.35)
          .style('stroke', isSel ? 'var(--color-fg)' : 'none').style('stroke-width', 2).style('cursor', list.length ? 'pointer' : 'default');
        if (list.length) {
          svg.append('text').attr('x', xx + cw / 2).attr('y', yy + cellH / 2 + 4).attr('text-anchor', 'middle').style('fill', 'var(--color-fg)').style('font-size', '11px').style('pointer-events', 'none').text(String(list.length));
          cell.on('pointerenter', (e) => tip.show(e, [['tt-tip-date', `${domLabel(d)} · ${tierLabel(t)}`], ['tt-tip-title', list.slice(0, 8).map((r) => r.name).join(', ') + (list.length > 8 ? ` and ${list.length - 8} more` : '')]]))
            .on('pointerleave', tip.hide)
            .on('click', () => dash.setParams(isSel ? { sdom: '', stier: '' } : { sdom: d, stier: t }));
        }
      });
    });
  });

  dash.draw('fitbars', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const rows = dash.rows('supply').filter((r) => pass(r, p, { ignoreDom: true }));
    const doms = domIds().filter((d) => rows.some((r) => r.domain === d));
    if (!doms.length) { el.append(mk('div', 'tt-empty', 'No sources match the current filters.')); return; }
    const W = Math.max(el.clientWidth, 320), labelW = 132, barH = 16, gap = 8, top = 4;
    const H = top + doms.length * (barH + gap);
    const maxN = d3.max(doms, (d) => rows.filter((r) => r.domain === d).length) || 1;
    const x = d3.scaleLinear([0, maxN], [0, W - labelW - 36]);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img').attr('aria-label', 'Fit by domain');
    const tip = T.tip(el);
    doms.forEach((d, i) => {
      const yy = top + i * (barH + gap);
      const lt = svg.append('text').attr('x', 4).attr('y', yy + barH - 4).style('fill', 'var(--color-fg)').style('font-size', '12px').text(domLabel(d));
      T.fit(lt.node(), labelW - 8);
      let xx = labelW;
      const inDom = rows.filter((r) => r.domain === d);
      for (const f of M.fits) {
        const list = inDom.filter((r) => r.fit === f.id);
        if (!list.length) continue;
        const w = x(list.length);
        svg.append('rect').attr('x', xx).attr('y', yy).attr('width', Math.max(1, w - 1)).attr('height', barH).attr('rx', 2).style('fill', T.fitColor(f.id)).style('cursor', 'pointer')
          .on('pointerenter', (e) => tip.show(e, [['tt-tip-date', `${domLabel(d)} · ${f.label}`], ['tt-tip-title', `${list.length} sources: ` + list.slice(0, 8).map((r) => r.name).join(', ') + (list.length > 8 ? '…' : '')]]))
          .on('pointerleave', tip.hide)
          .on('click', () => dash.setParams({ sdom: d, sfit: f.id }));
        xx += w;
      }
      svg.append('text').attr('x', xx + 6).attr('y', yy + barH - 4).style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text(String(inDom.length));
    });
  });

  dash.draw('fitlegend', (ul) => {
    ul.replaceChildren();
    for (const f of M.fits) { const li = mk('li'); li.append(T.chipSwatch(T.fitColor(f.id)), document.createTextNode(f.label)); ul.append(li); }
  });

  dash.draw('supplyrows', (tb) => {
    tb.replaceChildren();
    const p = dash.params();
    const order = domIds();
    const rows = dash.rows('supply').filter((r) => pass(r, p)).sort((a, b) => (a.domain === b.domain ? String(a.name).localeCompare(String(b.name)) : order.indexOf(a.domain) - order.indexOf(b.domain)));
    for (const r of rows) {
      const tr = mk('tr');
      tr.dataset.key = r.id;
      if (r.id === p.ssel) tr.className = 'is-sel';
      [r.name, domLabel(r.domain), tierLabel(r.access_tier), r.pricing_model, r.commercial_use, fitLabel(r.fit)].forEach((v, i) => tr.append(mk('td', i === 3 || i === 4 ? 'tt-hide-narrow' : null, v == null ? '' : String(v))));
      tb.append(tr);
    }
  });

  dash.draw('supplycount', (el) => { el.textContent = d3.format(',')(dash.rows('supply').filter((r) => pass(r, dash.params())).length); });

  dash.draw('supplydetail', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const r = p.ssel ? dash.rows('supply').find((x) => x.id === p.ssel) : null;
    if (!r) return;
    const clear = mk('button', 'tt-btn', 'Clear selection');
    clear.onclick = () => dash.setParams({ ssel: null });
    el.append(
      mk('h3', null, r.name),
      mk('div', 'tt-dmeta', [r.provider_org, domLabel(r.domain), r.subcategory].filter(Boolean).join(' · ')),
      mk('p', 'tt-dtext', r.what || ''),
      T.dl([
        ['Fit', fitLabel(r.fit) + (r.fit_reason ? ': ' + r.fit_reason : '')],
        ['Access', tierLabel(r.access_tier)], ['API', r.api], ['Auth', r.auth], ['Pricing', r.pricing_model], ['Price points', r.price_points], ['Rate limits', r.rate_limits],
        ['Commercial use', r.commercial_use], ['Resale', r.resale_allowed], ['Scale', r.scale],
        ['Website', r.url ? T.links(r.url) : null], ['Terms', r.terms_url ? T.links(r.terms_url) : null],
        ['Notes', r.notes], ['Confidence', r.confidence], ['Sources', (r.sources || []).length ? T.sourceList(r.sources) : null],
      ]),
      clear,
    );
  });

  dash.draw('demandbars', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const rows = byPriority();
    if (!rows.length) { el.append(mk('div', 'tt-empty', 'No demand segments in this bundle.')); return; }
    const W = Math.max(el.clientWidth, 320), labelW = Math.min(240, W * 0.45), barH = 18, gap = 8;
    const H = rows.length * (barH + gap) + 4;
    const x = d3.scaleLinear([0, 5], [0, W - labelW - 30]);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).attr('role', 'img').attr('aria-label', 'Demand segments by priority');
    const tip = T.tip(el);
    rows.forEach((r, i) => {
      const yy = 2 + i * (barH + gap);
      const v = Number(r.priority_score) || 0;
      const isSel = r.id === p.seg;
      const lt = svg.append('text').attr('x', 4).attr('y', yy + barH - 5).style('fill', 'var(--color-fg)').style('font-size', '12px').style('font-weight', isSel ? '600' : '400').text(r.segment);
      T.fit(lt.node(), labelW - 8);
      svg.append('rect').attr('class', 'tt-mark').attr('x', labelW).attr('y', yy).attr('width', Math.max(2, x(v))).attr('height', barH).attr('rx', 3)
        .style('fill', dash.colors[0]).style('fill-opacity', isSel ? 1 : 0.65).style('stroke', isSel ? 'var(--color-fg)' : 'none')
        .on('pointerenter', (e) => tip.show(e, [['tt-tip-title', r.segment], ['tt-tip-meta', `Priority ${v}`], ['tt-tip-meta', r.size_estimate]]))
        .on('pointerleave', tip.hide)
        .on('click', () => dash.setParams({ seg: isSel ? null : r.id }));
      svg.append('text').attr('x', labelW + x(v) + 6).attr('y', yy + barH - 5).style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text(String(v || ''));
    });
  });

  dash.draw('demanddetail', (el) => {
    el.replaceChildren();
    const r = segRow(dash.params());
    if (!r) return;
    const linked = dash.rows('supply').filter((s) => matches(r, s));
    const clear = mk('button', 'tt-btn', 'Clear segment');
    clear.onclick = () => dash.setParams({ seg: null });
    el.append(
      mk('h3', null, r.segment),
      mk('div', 'tt-dmeta', r.examples || ''),
      T.dl([
        ['Priority', r.priority_score], ['Size', r.size_estimate], ['How sized', r.size_basis], ['Budget', r.annual_budget], ['Tools today', r.current_tools],
        ['Jobs to be done', r.jobs_to_be_done], ['Pains', r.pains], ['Depends on', linked.map((s) => s.name).join(', ')],
        ['Channels', r.channels], ['Willingness to pay', r.wtp], ['Buying process', r.buying_process],
        ['Confidence', r.confidence], ['Sources', (r.sources || []).length ? T.sourceList(r.sources) : null],
      ]),
      clear,
    );
  });

  dash.draw('sdmatrix', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const supply = dash.rows('supply');
    const segs = byPriority();
    const doms = domIds().filter((dd) => supply.some((r) => r.domain === dd));
    if (!segs.length || !doms.length) { el.append(mk('div', 'tt-empty', 'No demand segments in this bundle.')); return; }
    const cnt = segs.map((sg) => doms.map((dd) => supply.filter((r) => r.domain === dd && matches(sg, r)).length));
    const maxC = d3.max(cnt.flat()) || 1;
    const W = Math.max(el.clientWidth, 640), labelW = 200, top = 70, cellH = 24;
    const cw = (W - labelW - 8) / doms.length;
    const H = top + segs.length * cellH + 6;
    const op = d3.scaleLinear([0, maxC], [0.08, 0.9]);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).style('min-width', '640px').attr('role', 'img').attr('aria-label', 'Which segments depend on which domains');
    doms.forEach((dd, j) => {
      const cx = labelW + j * cw + cw / 2;
      svg.append('text').attr('transform', `translate(${cx},${top - 8}) rotate(-35)`).style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text(domLabel(dd));
    });
    const tip = T.tip(el);
    segs.forEach((sg, i) => {
      const yy = top + i * cellH;
      const lt = svg.append('text').attr('x', 4).attr('y', yy + cellH / 2 + 4).style('fill', 'var(--color-fg)').style('font-size', '11px').style('font-weight', sg.id === p.seg ? '600' : '400').text(sg.segment);
      T.fit(lt.node(), labelW - 8);
      doms.forEach((dd, j) => {
        const n = cnt[i][j];
        const xx = labelW + j * cw;
        const rect = svg.append('rect').attr('class', 'tt-cell').attr('x', xx + 1.5).attr('y', yy + 1.5).attr('width', cw - 3).attr('height', cellH - 3).attr('rx', 2)
          .style('fill', n ? dash.colors[1] : 'var(--cds-chart-grid)').style('fill-opacity', n ? op(n) : 0.3).style('cursor', n ? 'pointer' : 'default');
        if (n) {
          if (cw > 18) svg.append('text').attr('x', xx + cw / 2).attr('y', yy + cellH / 2 + 4).attr('text-anchor', 'middle').style('font-size', '10px').style('fill', 'var(--color-fg)').style('pointer-events', 'none').text(String(n));
          rect.on('pointerenter', (e) => tip.show(e, [['tt-tip-date', `${sg.segment} · ${domLabel(dd)}`], ['tt-tip-title', supply.filter((r) => r.domain === dd && matches(sg, r)).map((r) => r.name).slice(0, 8).join(', ')]]))
            .on('pointerleave', tip.hide)
            .on('click', () => dash.setParams({ seg: sg.id, sdom: dd, stier: '' }));
        }
      });
    });
  });
})();
