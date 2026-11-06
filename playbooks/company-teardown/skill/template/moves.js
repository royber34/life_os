(() => {
  const T = window.tt;
  const { B, mk } = T;
  const MOVES = (B.prose || {}).moves;

  // So-what bands sit at the top of the evidence tabs. An empty band hides itself.
  for (const n of document.querySelectorAll('[data-band]')) {
    const text = ((B.prose || {}).bands || {})[n.dataset.band];
    n.hidden = !text;
    if (!text) continue;
    n.classList.add('tt-band');
    n.append(mk('span', 'tt-band-label', 'So what'));
    const body = mk('div', 'tt-prose');
    T.md(text, body, { listClass: 'tt-findings' });
    n.append(body);
  }
  for (const n of document.querySelectorAll('[data-has-moves]')) n.hidden = !MOVES;
  if (!MOVES) return;

  const TYPES = [
    ['find_out', 'Open questions', 'Low-cost checks that bear on the larger areas.'],
    ['double_down', 'Double-down candidates', 'Public data shows what the company keeps doing, and rarely shows results.'],
    ['quick_win', 'Quick wins', 'Specific gaps found in the research.'],
    ['dealer', MOVES.partner_label || 'Partners and channel', 'Often a large channel, and the least visible from outside.'],
    ['budget', 'Possible budget shifts', 'Spend is not public, so these show direction and breakeven figures, with no dollar split.'],
    ['bet', 'Larger questions', 'Areas that shape the business and carry real money or margin.'],
  ];
  const typeLabel = (t) => (TYPES.find((x) => x[0] === t) || [t, t])[1];
  const typeColor = (t) => dash.colors[Math.max(0, TYPES.findIndex((x) => x[0] === t)) % dash.colors.length];
  const LEVEL = { high: 'High', low: 'Low' };
  const items = MOVES.items || [];
  const number = new Map(items.map((m, i) => [m.id, i + 1]));
  const once = (el, fn) => { if (el.dataset.done) return; el.dataset.done = '1'; fn(); };
  const mdInto = (cls, text, opts) => { const n = mk('div', cls); T.md(text, n, opts); return n; };
  const dot = (m) => { const n = mk('span', 'tt-move-n', String(number.get(m.id))); n.style.background = typeColor(m.type); return n; };
  // A move inside the expanded view opens it first, so a jump never lands on hidden content.
  const jump = (id) => {
    const t = document.getElementById(`move-${id}`);
    if (!t) return;
    const d = t.closest('details');
    if (d) d.open = true;
    t.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };
  const moveButton = (m) => {
    const b = mk('button', 'tt-matrix-item');
    b.append(dot(m), mk('span', null, m.short));
    b.onclick = () => jump(m.id);
    return b;
  };

  dash.draw('movesfacts', (el) => once(el, () => {
    for (const h of MOVES.headlines || []) {
      const c = mk('div', 'tt-kpi tt-fact');
      c.append(mdInto('tt-kpi-value', h.value), mdInto('tt-fact-label tt-prose', h.label));
      if (h.kind) c.append(mk('span', 'tt-tag', h.kind));
      el.append(c);
    }
  }));

  dash.draw('movesanswer', (el) => once(el, () => {
    const a = MOVES.answer || {};
    const c = mk('section', 'tt-card');
    const head = mk('div', 'tt-card-head');
    head.append(mk('h2', null, a.heading || 'Identified areas'));
    if (a.reader) head.append(mk('p', 'tt-note', a.reader));
    c.append(head, mdInto('tt-verdict tt-prose', a.body || ''));
    if (a.top3) c.append(mdInto('tt-top3 tt-prose', a.top3));
    if (a.first) { c.append(mk('h3', null, 'Dates that bear on these')); c.append(mdInto('tt-prose', a.first, { listClass: 'tt-findings' })); }
    el.append(c);
  }));

  dash.draw('movesrules', (el) => once(el, () => {
    const a = MOVES.answer || {};
    const c = el;
      const t = mk('table', 'tt-plan tt-rules');
      const hr = mk('tr');
      for (const h of ['If internal numbers show', 'It would suggest', 'Areas']) hr.append(mk('th', null, h));
      const th = mk('thead'); th.append(hr);
      const tb = mk('tbody');
      for (const r of MOVES.rules) {
        const tr = mk('tr');
        const a1 = mk('td'); T.md(r.if, a1);
        const a2 = mk('td'); T.md(r.then, a2);
        const a3 = mk('td', 'tt-rule-moves');
        for (const id of r.moves || []) { const m = items.find((x) => x.id === id); if (m) { const b = mk('button', 'tt-chip', `${number.get(id)}`); b.title = m.short; b.onclick = () => jump(id); a3.append(b); } }
        tr.append(a1, a2, a3);
        tb.append(tr);
      }
      t.append(th, tb);
      c.append(t);
      if (a.rules_note) c.append(mk('p', 'tt-note', a.rules_note));
  }));

  const sowItem = (it) => {
    const c = T.insightCard(it);
    for (const id of it.moves || []) {
      const m = items.find((x) => x.id === id);
      if (m) { const b = mk('button', 'tt-chip', `${number.get(id)}. ${m.short}`); b.onclick = () => jump(id); c.append(b); }
    }
    return c;
  };
  dash.draw('sowopps', (el) => once(el, () => { for (const it of MOVES.opportunities || []) el.append(sowItem(it)); }));
  dash.draw('sowworking', (el) => once(el, () => {
    for (const [key, label, cls] of [['working', "What's working", 'is-working'], ['not_working', "What isn't", 'is-not']]) {
      const col = mk('div', `tt-lens-col ${cls}`);
      col.append(mk('span', 'tt-lens-label', label));
      for (const it of MOVES[key] || []) col.append(sowItem(it));
      el.append(col);
    }
  }));

  const QUADS = [['strengths', 'Strengths', 'Inside, helps'], ['weaknesses', 'Weaknesses', 'Inside, hurts'], ['opportunities', 'Opportunities', 'Outside, helps'], ['threats', 'Threats', 'Outside, hurts']];
  dash.draw('movesswot', (el) => once(el, () => {
    for (const [key, label, hint] of QUADS) {
      const q = mk('section', 'tt-swot');
      q.dataset.quad = key;
      const head = mk('div', 'tt-swot-head');
      head.append(mk('h3', null, label), mk('span', 'tt-note', hint));
      q.append(head);
      for (const r of (MOVES.swot || {})[key] || []) {
        const row = mk('div', 'tt-swot-row');
        const top = mk('div', 'tt-prose');
        T.md(r.point, top);
        row.append(top);
        row.append(mdInto('tt-swot-so tt-prose', `**So what:** ${r.so_what}`));
        const tags = mk('div', 'tt-row');
        if (r.kind) tags.append(mk('span', 'tt-tag', r.kind));
        if (r.evidence !== 'medium') tags.append(mk('span', `tt-tag tt-ev-${r.evidence}`, r.evidence === 'strong' ? 'Strong evidence' : 'Thin evidence'));
        row.append(tags);
        q.append(row);
      }
      el.append(q);
    }
  }));

  dash.draw('movescross', (el) => once(el, () => {
    for (const x of MOVES.crossings || []) {
      const row = mk('div', 'tt-cross');
      row.append(mk('b', null, x.pair));
      row.append(mdInto('tt-prose', x.text));
      const ids = (x.moves || []).filter((id) => number.has(id));
      if (ids.length) {
        const nav = mk('div', 'tt-row');
        for (const id of ids) {
          const b = mk('button', 'tt-chip', `${number.get(id)}. ${items.find((m) => m.id === id).short}`);
          b.onclick = () => jump(id);
          nav.append(b);
        }
        row.append(nav);
      }
      el.append(row);
    }
  }));

  // One screen: priority moves first, the rest a click away, in either order.
  dash.draw('movesplan', (el) => once(el, () => {
    const whens = MOVES.when_order || [...new Set(items.map((m) => m.when))];
    const byWhen = (p, q) => whens.indexOf(p.when) - whens.indexOf(q.when) || number.get(p.id) - number.get(q.id);
    const byValue = (p, q) => (q.impact - q.effort) - (p.impact - p.effort) || q.impact - p.impact || number.get(p.id) - number.get(q.id);
    let sort = 'when', all = false;
    const bar = mk('div', 'tt-row');
    const bWhen = mk('button', 'tt-chip', 'By timing');
    const bValue = mk('button', 'tt-chip', 'By impact for the effort');
    const bAll = mk('button', 'tt-chip', '');
    bar.append(bWhen, bValue, bAll);
    const table = mk('table', 'tt-plan');
    const head = mk('tr');
    for (const h of ['Timing', 'Area', 'Channel', 'Impact', 'Effort', 'Depends on']) head.append(mk('th', null, h));
    const th = mk('thead'); th.append(head);
    const tb = mk('tbody');
    table.append(th, tb);
    const rows = new Map(items.map((m) => {
      const tr = mk('tr');
      tr.dataset.plan = m.id;
      if (m.priority) tr.dataset.priority = '1';
      const when = mk('td', 'tt-plan-when');
      const name = mk('td');
      name.append(moveButton(m));
      tr.append(when, name, mk('td', 'tt-plan-minor', m.channel), mk('td', 'tt-plan-minor', `${m.impact} of 5`), mk('td', 'tt-plan-minor', `${m.effort} of 5`), mk('td', 'tt-plan-minor', m.depends));
      return [m.id, { tr, when, m }];
    }));
    const others = items.filter((m) => !m.priority).length;
    const render = () => {
      bWhen.setAttribute('aria-pressed', String(sort === 'when'));
      bValue.setAttribute('aria-pressed', String(sort === 'value'));
      bAll.setAttribute('aria-pressed', String(all));
      bAll.textContent = all ? 'Show the main areas only' : `Show the other ${others} areas too`;
      let last = null;
      for (const m of [...items].sort(sort === 'when' ? byWhen : byValue)) {
        const r = rows.get(m.id);
        r.tr.hidden = !(all || m.priority);
        tb.append(r.tr);
        if (r.tr.hidden) continue;
        r.when.textContent = sort === 'when' && m.when === last ? '' : m.when;
        last = m.when;
      }
    };
    bWhen.onclick = () => { sort = 'when'; render(); };
    bValue.onclick = () => { sort = 'value'; render(); };
    bAll.onclick = () => { all = !all; render(); };
    render();
    el.append(bar, table);
  }));

  // Impact against effort on the real 1 to 5 ranks. Moves sharing a rank share a cell, so nothing drifts across a line.
  dash.draw('movesmatrix', (el) => once(el, () => {
    const grid = mk('div', 'tt-mgrid');
    grid.append(mk('div', 'tt-mgrid-y', 'Impact'));
    for (let impact = 5; impact >= 1; impact--) {
      grid.append(mk('div', 'tt-mgrid-rank', String(impact)));
      for (let effort = 1; effort <= 5; effort++) {
        const cell = mk('div', 'tt-mcell');
        if (impact >= 3 && effort <= 2) cell.classList.add('is-now');
        else if (impact >= 3) cell.classList.add('is-plan');
        for (const m of items.filter((d) => d.impact === impact && d.effort === effort)) {
          const b = dot(m);
          b.classList.add('tt-mdot');
          if (!m.priority) b.classList.add('is-other');
          b.setAttribute('role', 'button');
          b.setAttribute('tabindex', '0');
          b.title = `${number.get(m.id)}. ${m.short}`;
          b.onclick = () => jump(m.id);
          b.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); jump(m.id); } };
          cell.append(b);
        }
        grid.append(cell);
      }
    }
    grid.append(mk('div', 'tt-mgrid-corner'));
    for (let effort = 1; effort <= 5; effort++) grid.append(mk('div', 'tt-mgrid-rank', String(effort)));
    const axis = mk('div', 'tt-mgrid-x', 'Effort');
    const left = mk('div', 'tt-matrix-chart');
    left.append(grid, axis);
    const legend = mk('div', 'tt-row tt-mlegend');
    for (const [id, label] of TYPES) {
      if (!items.some((d) => d.type === id)) continue;
      const s = mk('span', 'tt-note');
      const sw = mk('i', 'tt-sw');
      sw.style.background = typeColor(id);
      s.append(sw, document.createTextNode(` ${label}`));
      legend.append(s);
    }
    const key = mk('span', 'tt-note');
    key.textContent = 'Green shading: higher impact for lower effort. Blue shading: higher impact, more effort. Ringed: a main area.';
    left.append(legend, key);
    const side = mk('ol', 'tt-matrix-list');
    for (const d of items) { const li = mk('li'); li.append(moveButton(d)); side.append(li); }
    el.classList.add('tt-matrix');
    el.append(left, side);
  }));

  const field = (label, text) => {
    if (!text) return null;
    const f = mk('div', 'tt-mfield');
    f.append(mk('span', 'tt-flabel', label), mdInto('tt-prose', text));
    return f;
  };
  const card = (m, showType) => {
    const c = mk('section', 'tt-card tt-move');
    c.id = `move-${m.id}`;
    c.dataset.type = m.type;
    const head = mk('div', 'tt-move-head');
    head.append(dot(m), mk('h3', null, m.title));
    c.append(head);
    const tags = mk('div', 'tt-row');
    if (showType) tags.append(mk('span', 'tt-tag', typeLabel(m.type)));
    tags.append(mk('span', 'tt-tag', `Impact ${m.impact} of 5`), mk('span', 'tt-tag', `Effort ${m.effort} of 5`), mk('span', 'tt-tag', m.when));
    if (LEVEL[m.confidence]) tags.append(mk('span', `tt-tag tt-ev-${m.confidence}`, `${LEVEL[m.confidence]} confidence`));
    c.append(tags);
    if (m.from && m.to) {
      const shift = mk('div', 'tt-shift');
      shift.append(mdInto('tt-prose', m.from), mk('span', 'tt-shift-arrow', '→'), mdInto('tt-prose', m.to));
      c.append(shift);
    }
    c.append(mdInto('tt-prose', m.what, { listClass: 'tt-findings' }));
    for (const f of [field('What would change it', m.trigger), field('Why', m.why), field('The money', m.money), field('Unknown', m.check_first)]) if (f) c.append(f);
    const more = mk('details', 'tt-more');
    more.append(mk('summary', null, 'Possible test, and how it could be wrong'));
    for (const f of [field('Possible test', m.test), field('What to watch', m.watch), field('If wrong', m.if_wrong)]) if (f) more.append(f);
    c.append(more);
    if (m.goto) { const nav = mk('div', 'tt-nav'); nav.append(T.gotoButton(m.goto, m.goto_label)); c.append(nav); }
    return c;
  };
  dash.draw('moveslist', (el) => once(el, () => {
    const top = items.filter((m) => m.priority);
    const rest = items.filter((m) => !m.priority);
    const part = mk('div', 'tt-part');
    part.append(mk('h2', null, `The ${top.length} main areas`), mk('p', 'tt-note', 'Confidence is medium unless marked. It rates the area, separate from how each fact was sourced.'));
    el.append(part);
    const grid = mk('div', 'tt-grid2 tt-priority');
    for (const m of top) grid.append(card(m, true));
    el.append(grid);
    if (!rest.length) return;
    const all = mk('details', 'tt-allmoves');
    const names = TYPES.filter(([id]) => rest.some((m) => m.type === id)).map(([, l]) => l).join(', ');
    const sum = mk('summary');
    sum.append(mk('b', null, `The other ${rest.length} areas`), mk('span', 'tt-note', ` ${names}`));
    all.append(sum);
    for (const [id, label, note] of TYPES) {
      const list = rest.filter((m) => m.type === id);
      if (!list.length) continue;
      const p = mk('div', 'tt-part');
      p.append(mk('h2', null, label), mk('p', 'tt-note', note));
      all.append(p);
      const g = mk('div', 'tt-grid2');
      for (const m of list) g.append(card(m, false));
      all.append(g);
    }
    el.append(all);
  }));

  dash.draw('movesrequest', (el) => once(el, () => {
    const t = mk('table', 'tt-plan tt-rules');
    const hr = mk('tr');
    for (const h of ['Internal data', 'Who holds it', 'What it bears on']) hr.append(mk('th', null, h));
    const th = mk('thead'); th.append(hr);
    const tb = mk('tbody');
    for (const r of MOVES.data_request || []) {
      const tr = mk('tr');
      tr.append(mk('td', null, r.data), mk('td', 'tt-plan-minor', r.holder), mk('td', 'tt-plan-minor', r.decides));
      tb.append(tr);
    }
    t.append(th, tb);
    el.append(t);
  }));

  dash.draw('moveslimits', (el) => once(el, () => {
    T.md(MOVES.limits || '', el, { listClass: 'tt-findings' });
  }));
})();
