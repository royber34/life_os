(() => {
  const T = window.tt;
  const { COMP, mk } = T;
  const GROUPS = (COMP.groups || []).map((g) => g.id);
  const COMPS = COMP.components || [];
  const SCORES = COMP.scores || [];
  const LEVELS = ['low', 'medium', 'high'];
  const grpLabel = (v) => { const g = (COMP.groups || []).find((x) => x.id === v); return g ? g.label : v; };
  const axisLabel = (k) => { const s = SCORES.find((x) => x.id === k); return s ? s.label : k; };
  const lvl = (v) => Math.max(0, LEVELS.indexOf(String(v || '').toLowerCase()));
  const score = (r, k) => { const n = Number((r.scores || {})[k]); return Number.isFinite(n) ? n : 0; };
  const pass = (r, p) => {
    if (p.cgrp && r.group !== p.cgrp) return false;
    if (p.cthreat && String(r.threat_level).toLowerCase() !== p.cthreat) return false;
    if (!T.confOk(r, { conf: p.cconf })) return false;
    return T.textOk(p.cq, r.name, r.org, r.overall, r.positioning, r.icp, r.business_model);
  };
  const rowsOf = (p) => dash.rows('competitors').filter((r) => pass(r, p));
  const pick = (r, p) => dash.setParams({ csel: p.csel === r.id ? null : r.id });
  window.tt.compRows = rowsOf;

  dash.draw('comprubric', (el) => {
    const p = dash.params();
    const parts = [p.cx, p.cy].map((k) => { const s = SCORES.find((x) => x.id === k); return s && s.rubric ? `${s.label}: ${s.rubric}` : null; }).filter(Boolean);
    el.textContent = parts.join(' ');
    el.hidden = !parts.length;
  });

  dash.draw('compmap', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const xk = p.cx, yk = p.cy;
    const rows = rowsOf(p);
    if (!rows.length) { el.append(mk('div', 'tt-empty', 'No players match the current filters.')); return; }
    const W = Math.max(el.clientWidth, 520), H = 440, m = { l: 44, r: 16, t: 14, b: 40 };
    const x = d3.scaleLinear([-0.5, 5.5], [m.l, W - m.r]);
    const y = d3.scaleLinear([-0.5, 5.5], [H - m.b, m.t]);
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).style('min-width', '520px').attr('role', 'img').attr('aria-label', `Players by ${axisLabel(xk)} and ${axisLabel(yk)}`);
    for (let i = 0; i <= 5; i += 1) {
      svg.append('line').attr('x1', x(i)).attr('x2', x(i)).attr('y1', m.t).attr('y2', H - m.b).style('stroke', 'var(--cds-chart-grid)');
      svg.append('line').attr('x1', m.l).attr('x2', W - m.r).attr('y1', y(i)).attr('y2', y(i)).style('stroke', 'var(--cds-chart-grid)');
      svg.append('text').attr('x', x(i)).attr('y', H - m.b + 14).attr('text-anchor', 'middle').style('font-size', '10px').style('fill', 'var(--color-fg-muted)').text(String(i));
      svg.append('text').attr('x', m.l - 8).attr('y', y(i) + 3).attr('text-anchor', 'end').style('font-size', '10px').style('fill', 'var(--color-fg-muted)').text(String(i));
    }
    svg.append('text').attr('x', (m.l + W - m.r) / 2).attr('y', H - 6).attr('text-anchor', 'middle').style('font-size', '11px').style('fill', 'var(--color-fg-muted)').text(`${axisLabel(xk)} →`);
    svg.append('text').attr('transform', `translate(12,${(m.t + H - m.b) / 2}) rotate(-90)`).attr('text-anchor', 'middle').style('font-size', '11px').style('fill', 'var(--color-fg-muted)').text(`${axisLabel(yk)} →`);
    const cells = d3.group(rows, (r) => `${score(r, xk)}|${score(r, yk)}`);
    const tip = T.tip(el);
    for (const list of cells.values()) {
      const n = list.length;
      list.sort((a, b) => lvl(b.threat_level) - lvl(a.threat_level));
      list.forEach((r, i) => {
        const ang = (i / Math.max(n, 1)) * Math.PI * 2;
        const rad = n > 1 ? Math.min(22, 7 + n * 2.2) : 0;
        const cx = x(score(r, xk)) + Math.cos(ang) * rad;
        const cy = y(score(r, yk)) + Math.sin(ang) * rad;
        const isSel = r.id === p.csel;
        const rr = r.id === COMP.self ? 9 : 5 + lvl(r.threat_level) * 2.5;
        svg.append('circle').attr('class', 'tt-mark').attr('cx', cx).attr('cy', cy).attr('r', rr).attr('tabindex', 0)
          .style('fill', T.groupColor(r.group)).style('fill-opacity', p.csel && !isSel ? 0.35 : 0.85)
          .style('stroke', isSel ? 'var(--color-fg)' : 'var(--color-panel)').style('stroke-width', isSel ? 2.5 : 1)
          .on('pointerenter', (e) => tip.show(e, [['tt-tip-title', r.name], ['tt-tip-meta', `${grpLabel(r.group)} · threat ${r.threat_level || 'n/a'} · partner ${r.partner_level || 'n/a'}`], ['tt-tip-date', r.positioning_line || '']]))
          .on('pointerleave', tip.hide)
          .on('click', () => pick(r, p))
          .on('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(r, p); } });
        if (n <= 5 || isSel) {
          // Players sharing a cell get their labels stacked at the side, so names never print over each other.
          const lx = n > 1 ? x(score(r, xk)) + rad + 14 : cx + rr + 3;
          const ly = n > 1 ? y(score(r, yk)) + 3 + (i - (n - 1) / 2) * 12 : cy + 3;
          const isSelf = r.id === COMP.self;
          const t = svg.append('text').attr('x', lx).attr('y', ly).style('font-size', '10px').style('fill', 'var(--color-fg)').style('pointer-events', 'none').style('font-weight', isSel || isSelf ? '600' : '400').text(r.short_name || r.name);
          T.fit(t.node(), 110);
        }
      });
    }
  });

  dash.draw('compgroups', (el) => {
    el.replaceChildren();
    const present = new Set(dash.rows('competitors').map((r) => r.group));
    const ul = mk('ul', 'tt-legend');
    for (const g of GROUPS.filter((gg) => present.has(gg))) {
      const li = mk('li');
      li.append(T.chipSwatch(T.groupColor(g)), document.createTextNode(grpLabel(g)));
      ul.append(li);
    }
    el.append(ul);
  });

  dash.draw('compmatrix', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const rows = rowsOf(p).sort((a, b) => lvl(b.threat_level) - lvl(a.threat_level) || String(a.name).localeCompare(String(b.name)));
    if (!rows.length) { el.append(mk('div', 'tt-empty', 'No players match the current filters.')); return; }
    const cols = [...COMPS.map((c) => ({ id: c.id, label: c.label, comp: true })), { id: 'threat', label: 'Threat' }, { id: 'partner', label: 'Partner potential' }];
    const W = Math.max(el.clientWidth, 640), labelW = 190, top = 78, cellH = 22;
    const cw = (W - labelW - 8) / cols.length;
    const H = top + rows.length * cellH + 4;
    const svg = d3.select(el).append('svg').attr('width', '100%').attr('viewBox', `0 0 ${W} ${H}`).style('min-width', '640px').attr('role', 'img').attr('aria-label', 'Which players cover each component');
    cols.forEach((k, j) => {
      const cx = labelW + j * cw + cw / 2;
      svg.append('text').attr('transform', `translate(${cx},${top - 8}) rotate(-35)`).style('fill', 'var(--color-fg-muted)').style('font-size', '11px').text(k.label);
    });
    const tip = T.tip(el);
    rows.forEach((r, i) => {
      const yy = top + i * cellH;
      const isSel = r.id === p.csel;
      const lt = svg.append('text').attr('x', 4).attr('y', yy + cellH / 2 + 4).style('fill', 'var(--color-fg)').style('font-size', '11px').style('font-weight', isSel ? '600' : '400').style('cursor', 'pointer').text(r.name).on('click', () => pick(r, p));
      T.fit(lt.node(), labelW - 8);
      cols.forEach((k, j) => {
        const xx = labelW + j * cw;
        let fill = 'var(--cds-chart-grid)', op = 0.3, label = '';
        if (k.comp) {
          const v = String((r.coverage || {})[k.id] || 'no').toLowerCase();
          if (v === 'yes') { fill = dash.colors[0]; op = 0.9; label = 'yes'; } else if (v === 'partial') { fill = dash.colors[0]; op = 0.4; label = 'partial'; } else label = 'no';
        } else {
          const v = String(r[`${k.id}_level`] || '').toLowerCase();
          const base = k.id === 'threat' ? 'var(--cds-chart-status-critical)' : dash.colors[2];
          if (v && v !== 'none') { fill = base; op = [0.25, 0.55, 0.9][lvl(v)]; }
          label = v || 'not rated';
        }
        svg.append('rect').attr('class', 'tt-cell').attr('x', xx + 1.5).attr('y', yy + 1.5).attr('width', cw - 3).attr('height', cellH - 3).attr('rx', 2)
          .style('fill', fill).style('fill-opacity', op).style('stroke', isSel ? 'var(--color-fg)' : 'none').style('cursor', 'pointer')
          .on('pointerenter', (e) => tip.show(e, [['tt-tip-title', r.name], ['tt-tip-meta', `${k.label}: ${label}`], ['tt-tip-date', k.comp ? '' : (r[`${k.id}_why`] || '')]]))
          .on('pointerleave', tip.hide)
          .on('click', () => pick(r, p));
      });
    });
  });

  dash.draw('compquad', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const rows = rowsOf(p);
    const hasNone = rows.some((r) => String(r.partner_level || 'none').toLowerCase() === 'none');
    const cols = (hasNone ? ['none'] : []).concat(LEVELS);
    const grid = mk('div', 'tt-quad');
    grid.style.gridTemplateColumns = `minmax(4.5rem, auto) repeat(${cols.length}, minmax(0, 1fr))`;
    grid.append(mk('div', 'tt-quad-h', ''));
    for (const pl of cols) grid.append(mk('div', 'tt-quad-h', `Partner potential: ${pl}`));
    for (const th of LEVELS.slice().reverse()) {
      grid.append(mk('div', 'tt-quad-h tt-quad-side', `Threat: ${th}`));
      for (const pl of cols) {
        const cell = mk('div', 'tt-quad-cell');
        const list = rows.filter((r) => r.id !== COMP.self && String(r.threat_level).toLowerCase() === th && String(r.partner_level || 'none').toLowerCase() === pl).sort((a, b) => String(a.name).localeCompare(String(b.name)));
        for (const r of list) {
          const b = mk('button', 'tt-chip', r.short_name || r.name);
          b.setAttribute('aria-pressed', String(r.id === p.csel));
          b.prepend(T.chipSwatch(T.groupColor(r.group)));
          b.title = `${r.name}: ${r.partner_shape || ''}`;
          b.onclick = () => pick(r, p);
          cell.append(b);
        }
        grid.append(cell);
      }
    }
    el.append(grid);
  });

  dash.draw('comprows', (tb) => {
    tb.replaceChildren();
    const p = dash.params();
    const rows = rowsOf(p).sort((a, b) => GROUPS.indexOf(a.group) - GROUPS.indexOf(b.group) || lvl(b.threat_level) - lvl(a.threat_level) || String(a.name).localeCompare(String(b.name)));
    if (p.csort === 'asc' || p.csort === 'desc') { rows.sort((a, b) => String(a.name).localeCompare(String(b.name))); if (p.csort === 'desc') rows.reverse(); }
    for (const r of rows) {
      const tr = mk('tr');
      tr.dataset.key = r.id;
      if (r.id === p.csel) tr.className = 'is-sel';
      [r.name, grpLabel(r.group), r.business_model, r.traction, r.funding, r.threat_level, r.partner_level].forEach((v, i) => tr.append(mk('td', i === 2 || i === 4 ? 'tt-hide-narrow' : null, v == null ? '' : String(v))));
      tb.append(tr);
    }
  });

  dash.draw('landrows', (tb) => {
    tb.replaceChildren();
    const p = dash.params();
    const rows = dash.rows('landscape').filter((r) => (!p.cgrp || r.group === p.cgrp) && T.confOk(r, { conf: p.cconf }) && T.textOk(p.cq, r.name, r.org, r.what, r.why_listed)).sort((a, b) => String(a.name).localeCompare(String(b.name)));
    for (const r of rows) {
      const tr = mk('tr');
      tr.dataset.key = r.id;
      if (r.id === p.csel) tr.className = 'is-sel';
      [r.name, r.org, grpLabel(r.group), r.what, r.confidence].forEach((v, i) => tr.append(mk('td', i === 1 || i === 4 ? 'tt-hide-narrow' : null, v == null ? '' : String(v))));
      tb.append(tr);
    }
  });

  dash.draw('compcount', (el) => { el.textContent = d3.format(',')(rowsOf(dash.params()).length); });

  dash.draw('compdetail', (el) => {
    el.replaceChildren();
    const p = dash.params();
    if (!p.csel) return;
    const clear = mk('button', 'tt-btn', 'Clear selection');
    clear.onclick = () => dash.setParams({ csel: null });
    const land = dash.rows('landscape').find((x) => x.id === p.csel);
    const r = dash.rows('competitors').find((x) => x.id === p.csel);
    if (!r && land) {
      el.append(
        mk('h3', null, land.name),
        mk('div', 'tt-dmeta', [land.org, grpLabel(land.group)].filter(Boolean).join(' · ')),
        mk('p', 'tt-dtext', land.what || ''),
        T.dl([['Why listed', land.why_listed], ['Website', land.url ? T.links(land.url) : null], ['Confidence', land.confidence], ['Source', land.source ? T.links(land.source) : null]]),
        clear,
      );
      return;
    }
    if (!r) return;
    const mv = mk('ul', 'tt-list');
    for (const m of r.recent_moves || []) {
      const li = mk('li');
      li.append(mk('b', null, `${m.date || ''} `), document.createTextNode(m.event || ''));
      if (m.source) { li.append(document.createTextNode(' ')); li.append(T.links(m.source)); }
      mv.append(li);
    }
    const cover = COMPS.map((k) => `${k.label}: ${(r.coverage || {})[k.id] || 'no'}`).join(' · ');
    const scores = SCORES.map((k) => `${k.label} ${score(r, k.id)}`).join(' · ');
    el.append(
      mk('h3', null, r.name),
      mk('div', 'tt-dmeta', [r.org, grpLabel(r.group), r.hq, r.founded ? `founded ${r.founded}` : null, r.ownership].filter(Boolean).join(' · ')),
      mk('p', 'tt-dtext', r.overall || ''),
      T.dl([
        ['Threat', r.threat_level ? `${r.threat_level}: ${r.threat_why || ''}` : null],
        ['Partner potential', r.partner_level ? `${r.partner_level} (${r.partner_shape || 'n/a'}): ${r.partner_why || ''}` : null],
        ['Positioning', r.positioning], ['Target users', r.icp], ['Business model', r.business_model], ['Pricing', r.pricing],
        ['Size', r.size], ['Revenue', r.revenue], ['Traction', r.traction], ['Funding', r.funding],
        ['Go to market', r.gtm], ['Moat', r.moat], ['Weaknesses', r.weaknesses],
        ['Coverage', COMPS.length ? cover : null], ["Scores, writer's judgement (0 to 5)", scores],
        ['Recent moves', (r.recent_moves || []).length ? mv : null], ['Gaps', r.gaps], ['Confidence', r.confidence],
        ['Sources', (r.sources || []).length ? T.sourceList(r.sources) : null],
      ]),
      clear,
    );
  });
})();
