(() => {
  const T = window.tt;
  const { B, mk } = T;
  const mdInto = (cls, text, opts) => { const n = mk('div', cls); T.md(text || '', n, opts); return n; };
  const AI = (B.prose || {}).ai;
  if (!AI) return;

  const table = (t) => {
    const sec = mk('div', 'tt-fieldtable');
    sec.append(mk('h4', null, t.title));
    if (t.note) sec.append(mdInto('tt-note tt-prose', t.note));
    const wrap = mk('div', 'tt-plan-wrap');
    const tb = mk('table', 'tt-plan tt-rules');
    const th = mk('thead');
    const hr = mk('tr');
    for (const h of t.columns) hr.append(mk('th', null, h));
    th.append(hr);
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
  const labelled = (pairs, into) => {
    for (const [label, text] of pairs) {
      if (!text) continue;
      const b = mk('div', `tt-plain${label === 'The idea' ? ' is-idea' : ''}`);
      b.append(mk('span', 'tt-plain-label', label), mdInto('tt-prose', text));
      into.append(b);
    }
  };

  // One finding: the takeaway and its number. What was found, why it matters and the idea open on click.
  const finding = (it) => {
    const d = mk('details', 'tt-mrow tt-ai-find');
    const sum = mk('summary');
    const main = mk('div', 'tt-mrow-main');
    main.append(mk('h3', null, it.title));
    if (it.stat) main.append(mdInto('tt-mrow-stat', it.stat));
    sum.append(main);
    d.append(sum);
    const body = mk('div', 'tt-mrow-body');
    labelled([['Found', it.found], ['Why it matters', it.matters], ['The idea', it.idea]], body);
    d.append(body);
    return d;
  };
  const useRow = (u) => {
    const d = mk('details', 'tt-mrow tt-ai-use');
    const sum = mk('summary');
    const main = mk('div', 'tt-mrow-main');
    main.append(mk('h3', null, u.title));
    if (u.top && u.idea) main.append(mdInto('tt-mrow-idea tt-prose', u.idea));
    const meters = mk('div', 'tt-mrow-meters');
    for (const [label, value] of [['Impact', u.impact], ['Effort', u.effort]]) {
      const w = mk('span', 'tt-meter-wrap');
      const m = mk('span', 'tt-meter');
      m.setAttribute('aria-label', `${label} ${value} of 5`);
      m.title = `${label} ${value} of 5, a judgement`;
      for (let i = 1; i <= 5; i++) m.append(mk('i', i <= value ? 'is-on' : null));
      w.append(mk('small', null, label), m);
      meters.append(w);
    }
    const tags = mk('div', 'tt-mrow-tags');
    tags.append(mk('span', 'tt-tag', `Evidence: ${u.evidence}`));
    sum.append(main, meters, tags);
    d.append(sum);
    const body = mk('div', 'tt-mrow-body');
    labelled([['The idea', u.top ? null : u.idea], ['The gap', u.gap], ['What comparable companies did', u.comparables], ['Tools and public prices', u.tools], ['Data it would need', u.data], ['Risks', u.risks], ['A small test', u.test]], body);
    d.append(body);
    return d;
  };

  let showPart = () => {};
  T.showAiPart = (id) => showPart(id);

  dash.draw('aiparts', (el) => {
    el.replaceChildren();
    const parts = [...(AI.parts || []).map((p) => ({ ...p, n: (p.findings || []).length })), ...(AI.uses ? [{ id: 'uses', title: AI.uses.title, short: 'Inside the company', n: (AI.uses.items || []).length, uses: AI.uses }] : [])];
    const bar = mk('div', 'tt-mfilters');
    const secs = new Map();
    const chips = new Map();
    let current = 'all';
    showPart = (id) => {
      current = id;
      for (const [k, b] of chips) b.setAttribute('aria-pressed', String(k === current));
      for (const [k, s] of secs) s.hidden = current !== 'all' && current !== k;
    };
    const add = (id, label) => { const b = mk('button', 'tt-chip', label); b.onclick = () => showPart(id); chips.set(id, b); bar.append(b); };
    add('all', 'Everything');
    for (const p of parts) add(p.id, `${p.short || p.title.split(':')[0]} (${p.n})`);
    if ((AI.score_tables || []).length) { const b = mk('button', 'tt-chip', 'GEO score'); b.onclick = () => T.follow('id:ai/ai-score'); bar.append(b); }
    el.append(bar);
    for (const part of parts) {
      const sec = mk('section', 'tt-card tt-ai-part');
      sec.dataset.part = part.id;
      sec.id = `part-${part.id}`;
      const head = mk('div', 'tt-card-head');
      head.append(mk('h2', null, part.title));
      if (part.intro_short) head.append(mdInto('tt-note tt-prose', part.intro_short));
      sec.append(head);
      const list = mk('div', 'tt-mrows');
      if (part.uses) {
        const items = part.uses.items || [];
        for (const x of items.filter((i) => i.top)) list.append(useRow(x));
        sec.append(list);
        const rest = items.filter((i) => !i.top);
        if (rest.length) {
          const all = mk('details', 'tt-fold-inner');
          all.append(mk('summary', null, `The other ${rest.length} areas`));
          const l2 = mk('div', 'tt-mrows');
          for (const x of rest) l2.append(useRow(x));
          all.append(l2);
          sec.append(all);
        }
        const more = mk('details', 'tt-fold-inner');
        more.append(mk('summary', null, 'The evidence behind these, and what peers have said'));
        if (part.uses.intro) more.append(mdInto('tt-prose', part.uses.intro));
        for (const t of part.uses.tables || []) more.append(table(t));
        sec.append(more);
      } else {
        for (const it of part.findings || []) list.append(finding(it));
        sec.append(list);
        if (part.swot) {
          const f = mk('details', 'tt-fold-inner');
          f.append(mk('summary', null, 'SWOT for content types and formats'));
          const s = mk('div', 'tt-ai-swot');
          for (const [k, label] of [['strengths', 'Strengths'], ['weaknesses', 'Weaknesses'], ['opportunities', 'Opportunities'], ['threats', 'Threats']]) {
            const q = mk('div', `tt-ai-q is-${k}`);
            q.append(mk('b', null, label));
            const ul = mk('ul', 'tt-findings');
            for (const line of part.swot[k] || []) { const li = mk('li'); T.md(line, li); ul.append(li); }
            q.append(ul);
            s.append(q);
          }
          f.append(s);
          sec.append(f);
        }
        if ((part.tables || []).length) {
          const f = mk('details', 'tt-fold-inner');
          f.append(mk('summary', null, `The data tables (${part.tables.length})`));
          if (part.intro) f.append(mdInto('tt-note tt-prose', part.intro));
          for (const t of part.tables) f.append(table(t));
          sec.append(f);
        }
      }
      secs.set(part.id, sec);
      el.append(sec);
    }
    showPart(current);
    if (AI.body || (AI.score_tables || []).length) {
      const f = mk('details', 'tt-card tt-fold');
      f.id = 'ai-score';
      f.append(mk('summary', null, 'Score and how this was read'));
      if (AI.body) f.append(mdInto('tt-prose', AI.body));
      for (const t of AI.score_tables || []) f.append(table(t));
      el.append(f);
    }
  });
})();
