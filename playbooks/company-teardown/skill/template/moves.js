(() => {
  const T = window.tt;
  const { B, mk } = T;
  const MOVES = (B.prose || {}).moves;
  const mdInto = (cls, text, opts) => { const n = mk('div', cls); T.md(text, n, opts); return n; };

  // The top of a tab: a headline, up to four visual key points, and doors to the next layer.
  // Scroll only once the tab has drawn. A target inside a closed fold opens it first.
  const TOPS = (B.prose || {}).top || {};
  const reveal = (el) => {
    if (!el) return;
    for (let d = el.closest('details'); d; d = d.parentElement && d.parentElement.closest('details')) d.open = true;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };
  const follow = (target) => {
    const [kind, value] = String(target).split(':');
    if (kind === 'move') { T.goTo('sowhat'); setTimeout(() => T.jumpMove && T.jumpMove(value), 150); return; }
    if (kind === 'tab' || kind === 'doc') { T.goTo(kind === 'doc' ? target : value); return; }
    const tab = kind === 'part' ? 'ai' : value.split('/')[0];
    const id = kind === 'part' ? `part-${value}` : value.split('/')[1];
    T.goTo(tab);
    setTimeout(() => { if (kind === 'part' && T.showAiPart) T.showAiPart(value); reveal(document.getElementById(id)); }, 150);
  };
  T.follow = follow;
  const VIZ = {
    dots: (v) => {
      const n = mk('div', 'tt-v-dots');
      for (let i = 0; i < v.d; i++) n.append(mk('i', i < v.n ? 'is-on' : null));
      return n;
    },
    pips: (v) => {
      const n = mk('div', 'tt-v-pips');
      (v.names || []).forEach((name, i) => {
        const r = mk('span', 'tt-v-pip');
        r.append(mk('i', i < v.n ? 'is-on' : null), document.createTextNode(name));
        n.append(r);
      });
      return n;
    },
    bars: (v) => {
      const n = mk('div', `tt-v-bars${v.stack ? ' is-stack' : ''}`);
      const max = v.max || Math.max(...v.rows.map((r) => r.value));
      for (const r of v.rows) {
        const row = mk('div', `tt-v-bar${r.focus ? ' is-focus' : ''}`);
        const track = mk('span', 'tt-v-track');
        const fill = mk('i');
        fill.style.width = `${(100 * r.value) / max}%`;
        track.append(fill);
        row.append(mk('span', 'tt-v-name', r.label), track, mk('span', 'tt-v-num', r.text || String(r.value)));
        n.append(row);
      }
      return n;
    },
    range: (v) => {
      const n = mk('div', 'tt-v-range');
      const track = mk('span', 'tt-v-track');
      const span = v.max - v.min;
      const fill = mk('i', v.assumed ? 'is-assumed' : null);
      fill.style.left = `${(100 * (v.lo - v.min)) / span}%`;
      fill.style.width = `${(100 * (v.hi - v.lo)) / span}%`;
      track.append(fill);
      const ends = mk('div', 'tt-v-ends');
      ends.append(mk('span', null, v.min_label || String(v.min)), mk('span', null, v.max_label || String(v.max)));
      n.append(track, ends);
      return n;
    },
    share: (v) => {
      const n = mk('div', 'tt-v-range');
      const track = mk('span', 'tt-v-track');
      const fill = mk('i');
      fill.style.left = '0';
      fill.style.width = `${(100 * v.part) / v.whole}%`;
      track.append(fill);
      const ends = mk('div', 'tt-v-ends');
      ends.append(mk('span', null, `${v.part} of ${v.whole}${v.unit ? ` ${v.unit}` : ''}`));
      n.append(track, ends);
      return n;
    },
  };
  const drawTop = (n, top) => {
    n.classList.add('tt-top');
    const h = mk('h2', 'tt-top-head');
    T.md(top.headline, h);
    n.append(h);
    if (top.note) n.append(mdInto('tt-top-note', top.note));
    const tiles = mk('div', 'tt-top-tiles');
    for (const t of top.points || []) {
      const c = mk('article', 'tt-top-tile');
      if (t.so) c.append(mk('h3', 'tt-top-so', t.so));
      c.append(mdInto('tt-top-value', t.value));
      c.append(mdInto('tt-top-label tt-prose', t.label));
      if (t.viz && VIZ[t.viz.type]) c.append(VIZ[t.viz.type](t.viz));
      if (t.means) {
        const w = mk('div', 'tt-top-means');
        w.append(mk('span', 'tt-plain-label', 'What it means'), mdInto('tt-prose', t.means));
        c.append(w);
      }
      const foot = mk('div', 'tt-top-foot');
      if (t.kind) foot.append(mk('span', 'tt-tag', t.kind));
      if (t.goto) { const b = mk('button', 'tt-top-link', `${t.goto_label || 'See more'} →`); b.onclick = () => follow(t.goto); foot.append(b); }
      c.append(foot);
      tiles.append(c);
    }
    n.append(tiles);
    if ((top.doors || []).length) {
      const d = mk('div', 'tt-top-doors');
      for (const x of top.doors) { const b = mk('button', 'tt-chip', x.label); b.onclick = () => follow(x.goto); d.append(b); }
      n.append(d);
    }
  };
  for (const n of document.querySelectorAll('[data-band]')) {
    const tab = n.dataset.band;
    const text = ((B.prose || {}).bands || {})[tab];
    const top = TOPS[tab];
    n.hidden = !(text || top);
    if (top) {
      drawTop(n, top);
      if (text) {
        const f = mk('details', 'tt-top-more');
        f.append(mk('summary', null, 'In a few sentences'), mdInto('tt-prose', text, { listClass: 'tt-findings' }));
        n.append(f);
      }
      continue;
    }
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
  const dot = (m) => { const n = mk('span', 'tt-move-n', String(number.get(m.id))); n.style.background = typeColor(m.type); return n; };
  // A jump clears the filters first, so it never lands on hidden content.
  let showEverything = () => {};
  const jump = (id) => {
    showEverything();
    const t = document.getElementById(`move-${id}`);
    if (!t) return;
    t.open = true;
    t.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };
  T.jumpMove = jump;

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
    const c = mk('div', 'tt-fold-body');
    if (a.reader) c.append(mk('p', 'tt-note', a.reader));
    c.append(mdInto('tt-verdict tt-prose', a.body || ''));
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
  // Opportunities, what's working and what isn't: one panel, one list at a time. Evidence folds.
  const signalRow = (it) => {
    const d = mk('details', 'tt-srow tt-insight');
    const sum = mk('summary');
    sum.append(mk('span', 'tt-srow-title', it.title));
    d.append(sum);
    const body = mk('div', 'tt-srow-body');
    if (it.proof) { const r = mk('div', 'tt-row'); r.append(mk('span', 'tt-tag', `Basis: ${it.proof}`)); body.append(r); }
    if (it.evidence) body.append(mdInto('tt-prose', it.evidence));
    if (it.use) { const u = mk('div', 'tt-plain is-idea'); u.append(mk('span', 'tt-plain-label', it.use_label || 'How it can be used'), mdInto('tt-prose', it.use)); body.append(u); }
    const chips = mk('div', 'tt-row');
    for (const id of it.moves || []) {
      const m = items.find((x) => x.id === id);
      if (m) { const b = mk('button', 'tt-chip', `${number.get(id)}. ${m.short}`); b.onclick = () => jump(id); chips.append(b); }
    }
    if (chips.children.length) body.append(chips);
    d.append(body);
    return d;
  };
  dash.draw('sowsignals', (el) => once(el, () => {
    const groups = [['opportunities', 'Opportunities'], ['working', "What's working"], ['not_working', "What isn't"]];
    const bar = mk('div', 'tt-row');
    const lists = groups.map(([key, label], i) => {
      const list = mk('div', 'tt-srows');
      list.dataset.signal = key;
      list.hidden = i !== 0;
      for (const it of MOVES[key] || []) list.append(signalRow(it));
      const b = mk('button', 'tt-chip', `${label} (${(MOVES[key] || []).length})`);
      b.setAttribute('aria-pressed', String(i === 0));
      b.onclick = () => {
        for (const x of bar.children) x.setAttribute('aria-pressed', String(x === b));
        for (const l of el.querySelectorAll('.tt-srows')) l.hidden = l !== list;
      };
      bar.append(b);
      return list;
    });
    el.append(bar, ...lists);
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
        const row = mk('details', 'tt-swot-row');
        const sum = mk('summary');
        T.md(r.point, sum);
        row.append(sum);
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
          b.onclick = () => T.follow(`move:${id}`);
          nav.append(b);
        }
        row.append(nav);
      }
      el.append(row);
    }
  }));

  // Impact against effort on the real 1 to 5 ranks. Moves sharing a rank share a cell, so nothing drifts across a line.
  const buildMatrix = () => {
    const el = mk('div');
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
    el.classList.add('tt-matrix');
    el.append(left);
    return el;
  };

  const field = (label, text) => {
    if (!text) return null;
    const f = mk('div', 'tt-mfield');
    f.append(mk('span', 'tt-flabel', label), mdInto('tt-prose', text));
    return f;
  };
  const meter = (label, value) => {
    const n = mk('span', 'tt-meter');
    n.setAttribute('aria-label', `${label} ${value} of 5`);
    n.title = `${label} ${value} of 5, a judgement`;
    for (let i = 1; i <= 5; i++) n.append(mk('i', i <= value ? 'is-on' : null));
    return n;
  };
  T.meter = meter;
  const row = (m) => {
    const d = mk('details', 'tt-mrow tt-move');
    d.id = `move-${m.id}`;
    d.dataset.type = m.type;
    if (m.priority) d.dataset.priority = '1';
    const sum = mk('summary');
    const main = mk('div', 'tt-mrow-main');
    main.append(mk('h3', null, m.title));
    if (m.stat) main.append(mdInto('tt-mrow-stat', m.stat));
    if (m.priority && m.idea) main.append(mdInto('tt-mrow-idea tt-prose', m.idea));
    const meters = mk('div', 'tt-mrow-meters');
    const a = mk('span', 'tt-meter-wrap'); a.append(mk('small', null, 'Impact'), meter('Impact', m.impact));
    const b = mk('span', 'tt-meter-wrap'); b.append(mk('small', null, 'Effort'), meter('Effort', m.effort));
    meters.append(a, b);
    const tags = mk('div', 'tt-mrow-tags');
    tags.append(mk('span', 'tt-tag', m.when));
    if (LEVEL[m.confidence]) tags.append(mk('span', `tt-tag tt-ev-${m.confidence}`, `${LEVEL[m.confidence]} confidence`));
    sum.append(dot(m), main, meters, tags);
    d.append(sum);
    const body = mk('div', 'tt-mrow-body');
    if (m.from && m.to) {
      const shift = mk('div', 'tt-shift');
      shift.append(mdInto('tt-prose', m.from), mk('span', 'tt-shift-arrow', '→'), mdInto('tt-prose', m.to));
      body.append(shift);
    }
    if (m.found) {
      for (const [label, text] of [['Found', m.found], ['Why it matters', m.matters], ['The idea', m.idea]]) {
        const p = mk('div', `tt-plain${label === 'The idea' ? ' is-idea' : ''}`);
        p.append(mk('span', 'tt-plain-label', label), mdInto('tt-prose', text));
        body.append(p);
      }
    }
    const grid = mk('div', 'tt-mrow-fields');
    for (const f of [m.found ? field('In detail', m.what) : field('The area', m.what), field('Evidence', m.why), field('The numbers', m.money), field('What would change it', m.trigger), field('Unknown', m.check_first), field('Depends on', m.depends), field('Channel', m.channel), field('Type', typeLabel(m.type)), field('Possible test', m.test), field('What to watch', m.watch), field('If wrong', m.if_wrong)]) if (f) grid.append(f);
    body.append(grid);
    if (m.goto) { const nav = mk('div', 'tt-nav'); nav.append(T.gotoButton(m.goto, m.goto_label)); body.append(nav); }
    d.append(body);
    return d;
  };
  dash.draw('moveslist', (el) => once(el, () => {
    const whens = MOVES.when_order || [...new Set(items.map((m) => m.when))];
    const byWhen = (p, q) => whens.indexOf(p.when) - whens.indexOf(q.when) || number.get(p.id) - number.get(q.id);
    const byValue = (p, q) => (q.impact - q.effort) - (p.impact - p.effort) || q.impact - p.impact || number.get(p.id) - number.get(q.id);
    const others = items.filter((m) => !m.priority);
    const state = { sort: 'num', type: null, view: 'list' };
    const bar = mk('div', 'tt-mfilters');
    const chip = (label, fn) => { const b = mk('button', 'tt-chip', label); b.onclick = fn; return b; };
    const bValue = chip('Most impact for the effort', () => { state.sort = state.sort === 'value' ? 'num' : 'value'; render(); });
    const bWhen = chip('By timing', () => { state.sort = state.sort === 'when' ? 'num' : 'when'; render(); });
    const bList = chip('List', () => { state.view = 'list'; render(); });
    const bMatrix = chip('Impact and effort chart', () => { state.view = 'matrix'; render(); });
    const typeSelect = mk('select', 'tt-mselect');
    typeSelect.setAttribute('aria-label', 'Type');
    typeSelect.append(new Option('All types', ''));
    for (const [id, label] of TYPES) if (items.some((m) => m.type === id)) typeSelect.append(new Option(label, id));
    typeSelect.onchange = () => { state.type = typeSelect.value || null; if (state.type) further.open = true; render(); };
    bar.append(typeSelect, bValue, bWhen, bList, bMatrix);
    const note = mk('p', 'tt-note', 'Impact and effort are judgements, ranked against each other. Open a row for the finding, evidence and how it could be tested.');
    const lists = mk('div', 'tt-mlists');
    const list = mk('div', 'tt-mrows tt-priority');
    const further = mk('details', 'tt-allmoves');
    const names = TYPES.filter(([id]) => others.some((m) => m.type === id)).map(([, l]) => l).join(', ');
    const sum = mk('summary');
    sum.append(mk('b', null, `Further moves (${others.length})`), mk('span', 'tt-note', ` ${names}`));
    const rest = mk('div', 'tt-mrows');
    further.append(sum, rest);
    lists.append(list);
    if (others.length) lists.append(further);
    const rows = new Map(items.map((m) => [m.id, row(m)]));
    const matrix = buildMatrix();
    const render = () => {
      bValue.setAttribute('aria-pressed', String(state.sort === 'value'));
      bWhen.setAttribute('aria-pressed', String(state.sort === 'when'));
      bList.setAttribute('aria-pressed', String(state.view === 'list'));
      bMatrix.setAttribute('aria-pressed', String(state.view === 'matrix'));
      typeSelect.value = state.type || '';
      lists.hidden = state.view !== 'list';
      matrix.hidden = state.view !== 'matrix';
      const ordered = [...items];
      if (state.sort === 'value') ordered.sort(byValue);
      if (state.sort === 'when') ordered.sort(byWhen);
      for (const m of ordered) {
        const r = rows.get(m.id);
        r.hidden = !!state.type && m.type !== state.type;
        (m.priority ? list : rest).append(r);
      }
    };
    showEverything = () => { state.type = null; state.view = 'list'; further.open = true; render(); };
    render();
    el.append(bar, note, lists, matrix);
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
  for (const f of document.querySelectorAll('[data-fold-count]')) {
    const n = f.dataset.foldCount.split('+').reduce((sum, key) => sum + (key === 'swot' ? Object.values(MOVES.swot || {}).reduce((a, v) => a + v.length, 0) : (MOVES[key] || []).length), 0);
    f.append(document.createTextNode(` (${n})`));
  }
})();
