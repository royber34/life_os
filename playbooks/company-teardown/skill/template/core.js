window.tt = (() => {
  const B = dash.bundle;
  const CFG = B.config;
  const META = B.meta;
  const CUTOFF = CFG.cutoff;
  const LANES = CFG.lanes || [];
  const CHANNELS = CFG.channels || [];
  const COMP = CFG.competition || { groups: [], scores: [], components: [] };
  const FAMCI = { money: 0, turning_point: 0, product: 1, growth: 2, people: 3 };
  const FAMLABEL = { turning_point: 'Turning points', money: 'Strategy and money', product: 'Product and tech', growth: 'Go-to-market and growth', people: 'Team and funding', risk: 'Legal and incidents' };
  const laneById = new Map(LANES.map((l) => [l.id, l]));
  const parse = d3.utcParse('%Y-%m-%d');
  const d = (s) => parse(String(s || '').slice(0, 10));
  const iso = d3.utcFormat('%Y-%m-%d');
  const allLanes = () => LANES.map((l) => l.id);
  const laneLabel = (lane) => (laneById.has(lane) ? laneById.get(lane).label : lane);
  const famColor = (fam) => (fam === 'risk' ? 'var(--cds-chart-status-critical)' : FAMCI[fam] == null ? 'var(--cds-chart-muted)' : dash.colors[FAMCI[fam]]);
  const color = (lane) => famColor((laneById.get(lane) || {}).family);
  const isTurning = (r) => r.kind !== 'span' && (laneById.get(r.lane) || {}).family === 'turning_point';

  // Each tab keeps its own filters. A view is the set of params for one prefix.
  const view = (prefix, p = dash.params()) => ({
    period: p[`${prefix}period`], basis: p[`${prefix}basis`], conf: p[`${prefix}conf`], q: p[`${prefix}q`],
    from: p[`${prefix}from`], to: p[`${prefix}to`], sort: p[`${prefix}sort`],
  });
  const periodRange = (id) => {
    const per = (CFG.periods || []).find((x) => x.id === id);
    if (id === 'all' || !per || !per.from || !per.to) return META.data_range.map(d);
    return [d(per.from), d(per.to)];
  };
  const domain = (v) => (v.from && v.to ? [d(v.from), d(v.to)] : periodRange(v.period));
  const basisOk = (r, v) => !((v.basis === 'fact' && r.basis !== 'fact') || (v.basis === 'inference' && r.basis !== 'inference'));
  const confOk = (r, v) => !((v.conf === 'hm' && r.confidence === 'low') || (v.conf === 'high' && r.confidence !== 'high'));
  const textOk = (q, ...parts) => !q || parts.join(' ').toLowerCase().includes(String(q).toLowerCase());
  const span = (r) => [d(r.date), r.kind === 'span' ? d(r.date_end || CUTOFF) : d(r.date)];
  const inRange = (r, d0, d1) => { const [a, b] = span(r); return a && a <= d1 && b >= d0; };
  const compact = (v) => Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(v);
  const fmtDate = d3.utcFormat('%b %-d, %Y');
  const mk = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; };
  const missing = (what) => mk('span', 'tt-missing', `missing: ${what}`);
  const tip = (host) => {
    const t = mk('div', 'tt-tip');
    t.hidden = true;
    host.append(t);
    const show = (ev, lines) => {
      t.replaceChildren(...lines.filter((l) => l && l[1]).map(([cls, text]) => mk('div', cls, text)));
      t.hidden = false;
      const hb = host.getBoundingClientRect();
      const x = ev.clientX - hb.left + host.scrollLeft;
      const y = ev.clientY - hb.top + host.scrollTop;
      const w = t.offsetWidth, h = t.offsetHeight;
      const maxX = host.scrollLeft + host.clientWidth - w - 4;
      t.style.left = Math.max(host.scrollLeft + 4, Math.min(x + 12, maxX)) + 'px';
      t.style.top = (y - h - 10 < 0 ? y + 14 : y - h - 10) + 'px';
    };
    return { show, hide: () => { t.hidden = true; } };
  };
  const fit = (textEl, max) => {
    let s = textEl.textContent;
    while (s.length > 3 && textEl.getComputedTextLength() > max) { s = s.slice(0, -2); textEl.textContent = s + '…'; }
  };
  const monthTick = (t) => (t.getUTCDate() !== 1 ? d3.utcFormat('%b %-d')(t) : t.getUTCMonth() === 0 ? d3.utcFormat('%Y')(t) : d3.utcFormat('%b')(t));
  const styleAxis = (ax, size = '11px') => {
    ax.attr('font-size', null).attr('font-family', null);
    ax.selectAll('text').style('fill', 'var(--color-fg-muted)').style('font-size', size);
    ax.selectAll('line').style('stroke', 'var(--cds-chart-axis)');
    return ax;
  };
  const links = (src) => {
    const frag = document.createDocumentFragment();
    const s = String(src || '');
    const urls = s.match(/https?:\/\/[^\s,;)]+/g) || [];
    if (!urls.length) { frag.append(document.createTextNode(s)); return frag; }
    urls.forEach((u, i) => { const a = mk('a', null, u); a.href = u; a.target = '_blank'; a.rel = 'noopener'; if (i) frag.append(document.createTextNode(' · ')); frag.append(a); });
    const rest = s.replace(/https?:\/\/[^\s,;)]+/g, '').replace(/[\s,;]+/g, ' ').trim();
    if (rest) frag.append(document.createTextNode(' (' + rest + ')'));
    return frag;
  };
  const sourceList = (list) => {
    const frag = document.createDocumentFragment();
    (list || []).forEach((u, i) => { if (i) frag.append(document.createTextNode(' · ')); frag.append(links(u)); });
    return frag;
  };
  const dl = (pairs) => {
    const el = mk('dl', 'tt-dl');
    for (const [k, v] of pairs) {
      if (v == null || v === '') continue;
      el.append(mk('dt', null, k));
      const dd = mk('dd');
      if (v instanceof Node) dd.append(v); else dd.textContent = Array.isArray(v) ? v.join(', ') : String(v);
      el.append(dd);
    }
    return el;
  };
  const byDate = (a, b) => (a.date === b.date ? (a.id < b.id ? -1 : 1) : a.date < b.date ? -1 : 1);
  const navButtons = (seq, id, key, label) => {
    const i = seq.findIndex((x) => x.id === id);
    const nav = mk('div', 'tt-nav');
    const prev = mk('button', 'tt-btn', 'Previous');
    const next = mk('button', 'tt-btn', 'Next');
    prev.disabled = i <= 0; next.disabled = i < 0 || i >= seq.length - 1;
    prev.onclick = () => { if (i > 0) dash.setParams({ [key]: seq[i - 1].id }); };
    next.onclick = () => { if (i >= 0 && i < seq.length - 1) dash.setParams({ [key]: seq[i + 1].id }); };
    const clear = mk('button', 'tt-btn', 'Clear selection');
    clear.onclick = () => dash.setParams({ [key]: null });
    nav.append(prev, next, clear);
    if (i >= 0) nav.append(mk('span', 'tt-count', `${i + 1} of ${seq.length} ${label}`));
    return nav;
  };

  // Citations. One popover shared by every [c:id] on the page.
  const citeNos = new Map();
  let pop = null;
  const closePop = () => { if (pop) { pop.remove(); pop = null; } };
  const openPop = (anchor, id, claim) => {
    closePop();
    pop = mk('div', 'tt-cite-pop');
    const isUrl = /^https?:\/\//.test(claim.source || '');
    const src = mk(isUrl ? 'a' : 'div', null, claim.source || 'No source recorded');
    if (isUrl) { src.href = claim.source; src.target = '_blank'; src.rel = 'noopener'; }
    pop.append(src, mk('div', 'tt-cite-status', `Verification: ${claim.status || 'unchecked'} (${id})`));
    document.body.append(pop);
    const a = anchor.getBoundingClientRect();
    const w = pop.offsetWidth, h = pop.offsetHeight;
    pop.style.left = Math.max(8, Math.min(a.left, window.innerWidth - w - 8)) + 'px';
    pop.style.top = (a.top - h - 6 < 0 ? a.bottom + 6 : a.top - h - 6) + 'px';
  };
  document.addEventListener('pointerdown', (e) => { if (pop && !pop.contains(e.target) && !e.target.closest('.tt-cite')) closePop(); });
  const cite = (id) => {
    const claim = (B.claims || {})[id];
    if (!claim) return missing(`citation ${id}`);
    if (!citeNos.has(id)) citeNos.set(id, citeNos.size + 1);
    const isUrl = /^https?:\/\//.test(claim.source || '');
    const a = mk('a', 'tt-cite', String(citeNos.get(id)));
    a.dataset.claim = id;
    a.tabIndex = 0;
    a.setAttribute('aria-label', `Source: ${claim.source || 'none'}. Verification: ${claim.status || 'unchecked'}`);
    if (isUrl) { a.href = claim.source; a.target = '_blank'; a.rel = 'noopener'; }
    let lastPointer = 'mouse';
    a.addEventListener('pointerenter', (e) => { lastPointer = e.pointerType; if (e.pointerType === 'mouse') openPop(a, id, claim); });
    a.addEventListener('focus', () => openPop(a, id, claim));
    a.addEventListener('pointerdown', (e) => { lastPointer = e.pointerType; });
    a.addEventListener('click', (e) => {
      // A touch has no hover: the first tap shows the popover, whose link opens the source.
      if (lastPointer !== 'mouse' || !isUrl) { e.preventDefault(); openPop(a, id, claim); }
    });
    return a;
  };
  const stat = (id, kind) => {
    const key = kind === 'kpi' ? `kpi:${id}` : id;
    const s = (B.stats || {})[key];
    if (!s || s.missing || s.text == null) return missing(`${kind} ${id}`);
    return mk('b', null, s.text);
  };

  // Tab navigation used by nav cards, prose and doc links.
  const TABS = ['overview', 'sowhat', 'timeline', 'gtm', 'ai', 'competition', 'market', 'deepdive'];
  const TABLABEL = { overview: 'Overview', sowhat: 'So what', timeline: 'Timeline', gtm: 'Go-to-market', ai: 'AI', competition: 'Competition', market: 'Market', deepdive: 'Deep dive' };
  const hasMoves = () => !!((B.prose || {}).moves);
  const firstTab = () => 'overview';
  const liveTabs = () => TABS.filter((t) => (t !== 'market' || CFG.market) && (t !== 'ai' || (B.prose || {}).ai));
  const goTo = (raw) => {
    const target = raw === 'moves' ? 'sowhat' : raw;
    if (String(target).startsWith('doc:')) {
      dash.setParams({ tab: 'deepdive', doc: String(target).slice(4), lq: null, lsec: null });
      dash.setLink('deepdive');
    } else {
      dash.setParams({ tab: target });
      dash.setLink(target);
    }
    window.scrollTo({ top: 0 });
  };
  const docTitle = (slug) => { const r = (B.library || []).find((x) => x.doc === slug); return r ? r.doc_title : slug; };
  const gotoButton = (target, label) => {
    const text = label || (String(target).startsWith('doc:') ? `Read: ${docTitle(String(target).slice(4))}` : `Open ${TABLABEL[target] || target}`);
    const b = mk('button', 'tt-btn', text);
    b.onclick = () => goTo(target);
    return b;
  };

  const chipSwatch = (bg, cls) => { const i = mk('i', `tt-sw${cls ? ' ' + cls : ''}`); i.style.background = bg; return i; };
  const channelIndex = (ch) => (ch.color_index == null ? CHANNELS.indexOf(ch) : ch.color_index);
  const channelColor = (k) => { const ch = CHANNELS.find((c) => c.id === k); return ch ? dash.colors[channelIndex(ch) % dash.colors.length] : 'var(--cds-chart-muted)'; };
  const groupColor = (g) => { const i = (COMP.groups || []).findIndex((x) => x.id === g); return dash.colors[Math.max(0, i) % dash.colors.length]; };
  const fitColor = (f) => { const i = ((CFG.market || {}).fits || []).findIndex((x) => x.id === f); return dash.colors[Math.max(0, i) % dash.colors.length]; };

  const OPTS = {
    periods: () => (CFG.periods || []).map((x) => [x.id, x.label]),
    basis: () => [['all', 'Facts and inferences'], ['fact', 'Facts only'], ['inference', 'Inferences only']],
    conf: () => [['all', 'Any confidence'], ['hm', 'High and medium'], ['high', 'High only']],
    groups: () => [['', 'All groups'], ...(COMP.groups || []).map((g) => [g.id, g.label])],
    threat: () => [['', 'Any threat level'], ['high', 'High threat'], ['medium', 'Medium threat'], ['low', 'Low threat']],
    scores: () => (COMP.scores || []).map((s) => [s.id, s.label]),
    domains: () => [['', 'All domains'], ...((CFG.market || {}).domains || []).map((x) => [x.id, x.label])],
    tiers: () => [['', 'All access tiers'], ...((CFG.market || {}).tiers || []).map((x) => [x.id, x.label])],
    fits: () => [['', 'Any fit'], ...((CFG.market || {}).fits || []).map((x) => [x.id, x.label])],
  };

  const buildDefaults = () => {
    const per = CFG.default_period || ((CFG.periods || [])[0] || {}).id || 'all';
    const scope = (x) => ({ [`${x}period`]: per, [`${x}basis`]: 'all', [`${x}conf`]: 'all', [`${x}q`]: null, [`${x}from`]: null, [`${x}to`]: null, [`${x}sort`]: 'asc' });
    return {
      tab: firstTab(),
      ...scope('t'), lanes: allLanes(), person: '', sel: null,
      metrics: (CFG.metric_cards || []).filter((c) => c.default).map((c) => c.id),
      ...scope('g'), gperiod: CFG.default_period_gtm || per, gch: CHANNELS.map((c) => c.id), glift: (CFG.response_curves || []).filter((c) => c.default).map((c) => c.id), gsel: null,
      cgrp: '', cthreat: '', cconf: 'all', cq: null, csel: null, csort: 'none', cx: COMP.default_x || '', cy: COMP.default_y || '',
      sdom: '', stier: '', sfit: '', sconf: 'all', sq: null, ssel: null, seg: null,
      doc: null, lq: null, lsec: null,
    };
  };

  const buildChips = (host, items, attr, param) => {
    for (const it of items) {
      const b = mk('button', 'tt-chip');
      b.setAttribute(attr, it.id);
      if (it.swatch) b.append(it.swatch);
      b.append(document.createTextNode(it.label));
      b.addEventListener('click', () => {
        const all = items.map((x) => x.id);
        const on = new Set(dash.params()[param] || []);
        if (on.has(it.id)) on.delete(it.id); else on.add(it.id);
        dash.setParams({ [param]: all.filter((m) => on.has(m)) });
      });
      host.append(b);
    }
  };

  const init = () => {
    dash.setDefaults(buildDefaults());
    document.title = META.name;
    for (const n of document.querySelectorAll('[data-text]')) {
      const key = n.dataset.text;
      n.textContent = key === 'name' ? META.name : key === 'lede' ? META.lede : key === 'market.title' ? (CFG.market || {}).title || '' : '';
    }
    const nav = document.querySelector('.tt-tabs');
    const tabOrder = liveTabs();
    for (const t of tabOrder) {
      const b = mk('button', 'tt-tab', TABLABEL[t]);
      b.dataset.tab = t;
      b.addEventListener('click', () => goTo(t));
      nav.append(b);
    }
    const hide = (sel, yes) => { for (const n of document.querySelectorAll(sel)) n.hidden = yes; };
    hide('[data-needs="metric_cards"]', !(CFG.metric_cards || []).length);
    hide('[data-needs="response_curves"]', !(CFG.response_curves || []).length);
    hide('[data-needs="competitors"]', !(B.competitors || []).length);
    hide('[data-needs="components"]', !(COMP.components || []).length || !(B.competitors || []).length);
    hide('[data-needs="landscape"]', !(B.landscape || []).length);
    hide('[data-hide-unless-empty="competitors"]', (B.competitors || []).length > 0 || (B.landscape || []).length > 0);
    hide('[data-prose="gtm.playbook"]', !((B.prose || {}).gtm || {}).playbook);

    const chips = (name) => document.querySelector(`[data-chips="${name}"]`);
    buildChips(chips('lanes'), LANES.map((l) => ({ id: l.id, label: l.label, swatch: chipSwatch(color(l.id), l.family === 'turning_point' ? 'is-diamond' : '') })), 'data-lane', 'lanes');
    buildChips(chips('metrics'), (CFG.metric_cards || []).map((c) => ({ id: c.id, label: c.title })), 'data-metric', 'metrics');
    buildChips(chips('channels'), CHANNELS.map((c) => ({ id: c.id, label: c.label, swatch: chipSwatch(channelColor(c.id)) })), 'data-grow', 'gch');
    buildChips(chips('curves'), (CFG.response_curves || []).map((c, i) => ({ id: c.id, label: c.label, swatch: chipSwatch(dash.colors[i % dash.colors.length]) })), 'data-glift', 'glift');
    window.tt.buildMetricCards(document.querySelector('[data-mcards]'));

    for (const s of document.querySelectorAll('select[data-opts]')) s.replaceChildren(...OPTS[s.dataset.opts]().map(([v, t]) => new Option(t, v)));
    const zoomClear = {};
    for (const x of ['t', 'g']) zoomClear[`${x}period`] = { [`${x}from`]: null, [`${x}to`]: null };
    for (const s of document.querySelectorAll('select[data-bind]')) s.addEventListener('change', () => dash.setParams({ [s.dataset.bind]: s.value, ...(zoomClear[s.dataset.bind] || {}) }));
    for (const q of document.querySelectorAll('input[data-q]')) {
      let timer;
      q.addEventListener('input', () => {
        clearTimeout(timer);
        timer = setTimeout(() => dash.setParams({ [q.dataset.q]: q.value.trim() || null, ...(q.dataset.q === 'lq' ? { lsec: null } : {}) }), 250);
      });
    }
    const act = (name, fn) => { for (const b of document.querySelectorAll(`[data-act="${name}"]`)) b.addEventListener('click', () => fn(b)); };
    act('lanes-all', () => dash.setParams({ lanes: allLanes() }));
    act('lanes-none', () => dash.setParams({ lanes: [] }));
    act('gch-all', () => dash.setParams({ gch: CHANNELS.map((c) => c.id) }));
    act('gch-none', () => dash.setParams({ gch: [] }));
    act('zoom-reset', (b) => dash.setParams({ [`${b.dataset.scope}from`]: null, [`${b.dataset.scope}to`]: null }));
    act('reset', () => dash.resetParams(['tab']));
    act('sort', (b) => {
      const k = `${b.dataset.scope}sort`;
      const cur = dash.params()[k];
      dash.setParams({ [k]: cur === 'asc' ? 'desc' : 'asc' });
    });
    act('comp-clear', () => dash.setParams({ cgrp: '', cthreat: '', cconf: 'all', cq: null, csel: null, csort: 'none' }));
    act('market-clear', () => dash.setParams({ sdom: '', stier: '', sfit: '', sconf: 'all', sq: null, ssel: null, seg: null }));
    for (const b of document.querySelectorAll('[data-jump]')) b.addEventListener('click', () => { const t = document.getElementById(b.dataset.jump); if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    for (const tb of document.querySelectorAll('tbody[data-rowkey]')) tb.addEventListener('click', (ev) => { const tr = ev.target.closest('tr[data-key]'); if (tr) dash.setParams({ [tb.dataset.rowkey]: tr.dataset.key }); });

    const fromHash = location.hash.slice(1);
    if (liveTabs().includes(fromHash)) dash.setParams({ tab: fromHash });

    dash.onData(() => {
      const p = dash.params();
      const tab = liveTabs().includes(p.tab) ? p.tab : firstTab();
      for (const s of document.querySelectorAll('[data-page]')) s.hidden = s.dataset.page !== tab;
      for (const b of document.querySelectorAll('[data-tab]')) b.setAttribute('aria-selected', String(b.dataset.tab === tab));
      const setPressed = (attr, list) => { const on = new Set(list || []); for (const b of document.querySelectorAll(`.tt-chip[${attr}]`)) b.setAttribute('aria-pressed', String(on.has(b.getAttribute(attr)))); };
      setPressed('data-lane', p.lanes);
      setPressed('data-metric', p.metrics);
      setPressed('data-grow', p.gch);
      setPressed('data-glift', p.glift);
      const mOn = new Set(p.metrics || []);
      for (const c of document.querySelectorAll('[data-mcard]')) c.hidden = !mOn.has(c.dataset.mcard);
      for (const s of document.querySelectorAll('select[data-bind]')) if (s !== document.activeElement) s.value = p[s.dataset.bind] == null ? '' : p[s.dataset.bind];
      for (const q of document.querySelectorAll('input[data-q]')) if (q !== document.activeElement) q.value = p[q.dataset.q] || '';
      for (const e of document.querySelectorAll('[data-hide-if]')) e.hidden = Boolean(p[e.dataset.hideIf]);
      for (const z of document.querySelectorAll('[data-zoomed]')) z.hidden = !(p[`${z.dataset.zoomed}from`] && p[`${z.dataset.zoomed}to`]);
      for (const th of document.querySelectorAll('th[data-sortable]')) {
        const v = p[`${th.dataset.sortable}sort`];
        th.setAttribute('aria-sort', v === 'desc' ? 'descending' : v === 'asc' ? 'ascending' : 'none');
      }
    });
    dash.start();
  };

  return { B, CFG, META, COMP, CUTOFF, LANES, CHANNELS, FAMLABEL, TABLABEL, laneById, d, iso, allLanes, laneLabel, famColor, color, isTurning, view, periodRange, domain, basisOk, confOk, textOk, span, inRange, compact, fmtDate, mk, missing, tip, fit, monthTick, styleAxis, links, sourceList, dl, byDate, navButtons, cite, stat, goTo, gotoButton, chipSwatch, channelColor, groupColor, fitColor, init };
})();

(() => {
  const T = window.tt;
  const { mk, B, CFG, META } = T;

  dash.draw('kpis', (el) => {
    el.replaceChildren();
    for (const k of CFG.kpis || []) {
      const s = (B.stats || {})[`kpi:${k.label}`];
      const card = mk('div', 'tt-kpi');
      const val = mk('div', 'tt-kpi-value');
      if (!s || s.missing || s.text == null) val.append(T.missing(k.metric || k.label)); else val.textContent = s.text;
      card.append(mk('div', 'tt-kpi-label', k.label), val);
      if (k.note) card.append(mk('div', 'tt-kpi-note', k.note));
      el.append(card);
    }
  });

  const VERIFY_CAVEAT = 'Accurate to sources means the claims match the sources cited. The sources can be wrong, and evidence that was never found does not show up here.';
  dash.draw('verification', (el) => {
    el.replaceChildren();
    const v = B.verification;
    if (!v) {
      const c = mk('section', 'tt-card tt-verify tt-verify-none');
      const trust = document.getElementById('trust');
      if (trust) trust.open = true;
      c.append(mk('h2', null, 'Not verified yet'), mk('p', 'tt-note', VERIFY_CAVEAT), mk('p', 'tt-note', 'No independent check of these claims has run. Treat every number and date here as unchecked.'));
      el.append(c);
      return;
    }
    const c = mk('section', 'tt-card tt-verify');
    c.append(mk('div', 'tt-card-head'));
    c.firstChild.append(mk('h2', null, `Verification: ${v.label || 'unlabelled'}`));
    c.append(mk('p', 'tt-note', VERIFY_CAVEAT));
    if (v.label === 'SECOND SAMPLE NEEDED') c.append(mk('p', 'tt-note', 'The wrong rate in the random sample is between 3 and 6 percent, which calls for a second check of the weakest workstream. Treat the numbers here as provisional until that check is done.'));
    const nums = mk('div', 'tt-verify-nums');
    const num = (label, value) => { const n = mk('div'); n.append(mk('b', null, value == null ? 'not recorded' : String(value)), document.createTextNode(label)); nums.append(n); };
    num('claims in the ledger', v.claims_total);
    num('claims checked', v.checked);
    if (v.random_checked != null) num('random rows checked', v.random_checked);
    if (v.load_bearing_checked != null) num('load-bearing rows checked', v.load_bearing_checked);
    for (const [k, n] of Object.entries(v.counts || {})) num(k, n);
    c.append(nums);
    const nums2 = mk('div', 'tt-verify-nums');
    const pct = (x) => d3.format('.1%')(x);
    const ci = v.wrong_rate_ci;
    const numTop = (label, value) => { const n = mk('div'); n.append(mk('b', null, value == null ? 'not recorded' : String(value)), document.createTextNode(label)); nums2.append(n); };
    numTop('estimated wrong rate', v.wrong_rate == null ? null : pct(v.wrong_rate) + (ci && ci.length === 2 ? ` (${pct(ci[0])} to ${pct(ci[1])})` : ''));
    numTop('sources unreachable', v.unreachable);
    c.append(nums2);
    c.append(mk('p', 'tt-note', 'The counts cover every check made, including targeted checks of the weakest rows. The wrong rate uses only the random sample, so the two differ.'));
    const ws = Object.entries(v.workstreams || {});
    (v.findings || []).filter((f) => ['Before corrections', 'Moves evidence', 'Sample too small'].some((x) => String(f).startsWith(x))).forEach((f) => c.append(mk('p', 'tt-note', f)));
    if (ws.length) {
      const more = mk('details', 'tt-more');
      more.append(mk('summary', null, 'The check by research area'));
      more.append(T.dl(ws.map(([k, l]) => [k, l])));
      if (ws.some(([, l]) => String(l).startsWith('TOO FEW TO RATE'))) more.append(mk('p', 'tt-note', 'TOO FEW TO RATE: under 20 rows were checked in that workstream, so it gets no rating of its own. One wrong row in a handful says little.'));
      c.append(more);
    }
    if (v.cutoff) c.append(mk('p', 'tt-note', `Evidence cutoff: ${v.cutoff}.`));
    el.append(c);
  });

  dash.draw('summary', (el) => {
    el.replaceChildren();
    const list = ((B.prose || {}).overview || {}).summary || [];
    for (const s of list) {
      const c = mk('div', 'tt-card');
      const head = mk('div', 'tt-card-head');
      head.append(mk('h2', null, s.heading));
      const body = mk('div', 'tt-prose');
      T.md(s.body, body, { listClass: 'tt-findings' });
      c.append(head, body);
      if (s.goto) { const nav = mk('div', 'tt-nav'); nav.append(T.gotoButton(s.goto, s.goto_label)); c.append(nav); }
      el.append(c);
    }
  });

  dash.draw('navcards', (el) => {
    el.replaceChildren();
    const c = META.counts || {};
    const cards = [
      ['sowhat', 'The moves, then opportunities, then what is working and what is not, with the competing readings.'],
      ['timeline', `Every dated event in ${(T.LANES || []).length} lanes, with growth charts on the same axis.`],
      ['gtm', 'Each launch, campaign, post and offer in order, sized by reach, against the traction it moved.'],
      ...((B.prose || {}).ai ? [['ai', 'How AI answer engines see the company, and inferred areas for using AI inside it.']] : []),
      ['competition', `${d3.format(',')(c.competitors || 0)} players profiled, scored and rated for threat and partner potential.`],
      ...(CFG.market ? [['market', 'Who supplies the adjacent market, on what terms, and who would buy.']] : []),
      ['deepdive', 'Every report in full, searchable, with sources.'],
    ];
    for (const [tab, text] of cards) {
      const b = mk('button', 'tt-navcard');
      b.append(mk('b', null, T.TABLABEL[tab]), mk('span', null, text));
      b.onclick = () => T.goTo(tab);
      el.append(b);
    }
  });

  const CARDKINDS = { verdict: 'verdict', implication: 'ins' };
  dash.draw('sowhat', (el) => {
    el.replaceChildren();
    const items = (B.prose || {}).so_what || [];
    const part = mk('div', 'tt-part');
    part.append(mk('h2', null, (B.prose || {}).moves ? 'Other readings and lessons' : `${META.name} on its own terms`), mk('p', 'tt-note', 'What the evidence means, what it teaches and what would change the reading. Readings are the writer\'s, built on the facts in the reports.'));
    el.append(part);
    if (!items.length) { el.append(T.missing('so what prose')); return; }
    let grid = null, gridKind = null, lastGroup = null;
    const flush = () => { grid = null; gridKind = null; };
    for (const s of items) {
      const kind = CARDKINDS[s.kind] || 'card';
      if (s.group !== lastGroup) { flush(); if (s.group) el.append(mk('span', 'tt-group', s.group)); lastGroup = s.group; }
      if (kind === 'verdict') {
        flush();
        const c = mk('section', 'tt-card');
        const head = mk('div', 'tt-card-head');
        head.append(mk('h2', null, s.heading));
        const body = mk('div', 'tt-verdict tt-prose');
        T.md(s.body, body);
        c.append(head, body);
        if (s.goto) { const nav = mk('div', 'tt-nav'); nav.append(T.gotoButton(s.goto, s.goto_label)); c.append(nav); }
        el.append(c);
        continue;
      }
      if (gridKind !== kind) { grid = mk('div', kind === 'ins' ? 'tt-grid3' : 'tt-grid2'); gridKind = kind; el.append(grid); }
      const c = mk(kind === 'ins' ? 'article' : 'section', kind === 'ins' ? 'tt-ins' : 'tt-card');
      c.dataset.kind = s.kind;
      if (kind === 'ins') c.append(mk('h3', null, s.heading));
      else { const head = mk('div', 'tt-card-head'); head.append(mk('h2', null, s.heading)); c.append(head); }
      const body = mk('div', 'tt-prose');
      T.md(s.body, body, { listClass: 'tt-findings' });
      c.append(body);
      if (s.goto) { const nav = mk('div', 'tt-nav'); nav.append(T.gotoButton(s.goto, s.goto_label)); c.append(nav); }
      grid.append(c);
    }
  });
})();
