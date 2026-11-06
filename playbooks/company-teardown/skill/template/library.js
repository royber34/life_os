(() => {
  const T = window.tt;
  const mk = T.mk;
  const safeLink = (text, url) => { const a = mk('a', null, text); a.href = url; a.target = '_blank'; a.rel = 'noopener'; return a; };
  const inline = (parent, text) => {
    const re = /(\[c:[^\]\s]+\]|\{\{(?:stat|kpi):[^}]+\}\}|\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\)|https?:\/\/[^\s<>)\]]+)/g;
    let last = 0, m;
    const s = String(text);
    while ((m = re.exec(s))) {
      if (m.index > last) parent.append(document.createTextNode(s.slice(last, m.index)));
      const tok = m[0];
      if (tok.startsWith('[c:')) parent.append(T.cite(tok.slice(3, -1)));
      else if (tok.startsWith('{{')) { const mm = /^\{\{(stat|kpi):(.*)\}\}$/.exec(tok); parent.append(T.stat(mm[2].trim(), mm[1])); }
      else if (tok.startsWith('**')) inline(parent.appendChild(mk('strong')), tok.slice(2, -2));
      else if (tok.startsWith('`')) parent.append(mk('code', null, tok.slice(1, -1)));
      else if (tok.startsWith('[')) {
        const mm = /^\[([^\]]+)\]\(([^)\s]+)\)$/.exec(tok);
        const href = mm[2];
        if (/^https?:\/\//.test(href)) parent.append(safeLink(mm[1], href));
        else parent.append(mk('span', 'tt-ref', mm[1]));
      } else { const url = tok.replace(/[.,;:]+$/, ''); parent.append(safeLink(url, url)); if (url.length < tok.length) parent.append(document.createTextNode(tok.slice(url.length))); }
      last = m.index + tok.length;
    }
    if (last < s.length) parent.append(document.createTextNode(s.slice(last)));
    return parent;
  };
  const render = (md, host, opts = {}) => {
    let anchor = opts.anchor;
    const listClass = opts.listClass || 'tt-list';
    const lines = String(md).replace(/\r/g, '').split('\n');
    let i = 0, list = null, para = [];
    const flushPara = () => {
      if (!para.length) return;
      const p = inline(mk('p'), para.join(' '));
      if (/^\*\*So what:?\*\*|^So what:/.test(para[0])) p.className = 'tt-sowhat';
      host.append(p);
      para = [];
    };
    const endList = () => { list = null; };
    while (i < lines.length) {
      const line = lines[i];
      if (/^```/.test(line)) {
        flushPara(); endList();
        const buf = [];
        i++;
        while (i < lines.length && !/^```/.test(lines[i])) { buf.push(lines[i]); i++; }
        host.append(mk('pre', 'tt-pre', buf.join('\n')));
        i++; continue;
      }
      const h = /^(#{1,4})\s+(.*)$/.exec(line);
      if (h) {
        flushPara(); endList();
        const el = inline(mk('h' + Math.min(6, h[1].length + 2), 'tt-lh'), h[2]);
        if (anchor) el.id = anchor;
        anchor = null;
        host.append(el); i++; continue;
      }
      if (/^\s*\|/.test(line)) {
        flushPara(); endList();
        const rows = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) { rows.push(lines[i]); i++; }
        const cells = (r) => r.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => c.trim());
        const wrap = mk('div', 'tt-ltable');
        const table = mk('table', 'tt-table');
        const body = rows.filter((r) => !/^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(r));
        body.forEach((r, k) => {
          const tr = mk('tr');
          for (const c of cells(r)) tr.append(inline(mk(k === 0 ? 'th' : 'td'), c));
          (k === 0 ? (table.tHead || table.createTHead()) : (table.tBodies[0] || table.createTBody())).append(tr);
        });
        wrap.append(table); host.append(wrap); continue;
      }
      const li = /^(\s*)([-*]|\d+\.)\s+(.*)$/.exec(line);
      if (li) {
        flushPara();
        const ordered = /\d/.test(li[2]);
        if (!list || list.ordered !== ordered) { list = { el: mk(ordered ? 'ol' : 'ul', listClass), ordered }; host.append(list.el); }
        const item = inline(mk('li'), li[3]);
        if (li[1].length >= 2) item.className = 'tt-sub';
        list.el.append(item); i++; continue;
      }
      if (/^>\s?/.test(line)) { flushPara(); endList(); host.append(inline(mk('blockquote', 'tt-quote'), line.replace(/^>\s?/, ''))); i++; continue; }
      if (/^\s*(---|\*\*\*)\s*$/.test(line)) { flushPara(); endList(); host.append(mk('hr', 'tt-hr')); i++; continue; }
      if (!line.trim()) { flushPara(); endList(); i++; continue; }
      if (list && /^\s{2,}\S/.test(line)) { const lastLi = list.el.lastElementChild; if (lastLi) inline(lastLi, ' ' + line.trim()); i++; continue; }
      endList();
      para.push(line.trim()); i++;
    }
    flushPara();
  };
  window.tt.md = render;

  const docsOf = (rows) => {
    const m = new Map();
    for (const r of rows) if (!m.has(r.doc)) m.set(r.doc, { doc: r.doc, title: r.doc_title, group: r.group, order: Number(r.doc_order) || 0 });
    return Array.from(m.values()).sort((a, b) => a.order - b.order);
  };

  dash.draw('libdocs', (el) => {
    el.replaceChildren();
    const p = dash.params();
    const docs = docsOf(dash.rows('library'));
    if (!docs.length) { el.append(mk('div', 'tt-empty', 'No documents in this bundle.')); return; }
    let group = null, ul = null;
    for (const doc of docs) {
      if (doc.group !== group) { group = doc.group; el.append(mk('div', 'tt-lgroup', group)); ul = mk('ul', 'tt-ldocs'); el.append(ul); }
      const b = mk('button', 'tt-ldoc', doc.title);
      b.setAttribute('aria-current', String(doc.doc === (p.doc || docs[0].doc)));
      b.onclick = () => dash.setParams({ doc: doc.doc, lq: null, lsec: null });
      const li = mk('li');
      li.append(b);
      ul.append(li);
    }
  });

  dash.draw('libhits', (el) => {
    el.replaceChildren();
    const p = dash.params();
    if (!p.lq) return;
    const q = String(p.lq).toLowerCase();
    const hits = dash.rows('library').filter((r) => String(r.md).toLowerCase().includes(q) || String(r.heading).toLowerCase().includes(q));
    el.append(mk('div', 'tt-count', `${hits.length} sections mention “${p.lq}”`));
    const ul = mk('ul', 'tt-hits');
    for (const r of hits.slice(0, 60)) {
      const txt = String(r.md);
      const k = txt.toLowerCase().indexOf(q);
      const snip = k >= 0 ? (k > 60 ? '…' : '') + txt.slice(Math.max(0, k - 60), k + 120).replace(/\s+/g, ' ') + '…' : '';
      const b = mk('button', 'tt-hit');
      b.append(mk('span', 'tt-hit-doc', r.doc_title), mk('span', 'tt-hit-head', r.heading || ''), mk('span', 'tt-hit-snip', snip));
      b.onclick = () => dash.setParams({ doc: r.doc, lsec: r.id, lq: null });
      const li = mk('li');
      li.append(b);
      ul.append(li);
    }
    el.append(ul);
  });

  dash.draw('libreader', (el) => {
    el.replaceChildren();
    const rows = dash.rows('library');
    const p = dash.params();
    if (p.lq) return;
    const docs = docsOf(rows);
    const docId = p.doc && docs.some((x) => x.doc === p.doc) ? p.doc : docs[0] && docs[0].doc;
    const secs = rows.filter((r) => r.doc === docId).sort((a, b) => Number(a.idx) - Number(b.idx));
    if (!secs.length) return;
    const head = mk('div', 'tt-lhead');
    head.append(mk('div', 'tt-dmeta', secs.length + ' sections'));
    const toc = mk('nav', 'tt-ltoc');
    for (const s of secs.filter((x) => x.heading && Number(x.level) <= 2)) {
      const b = mk('button', 'tt-btn', s.heading);
      b.onclick = () => { const t = document.getElementById('sec-' + s.id); if (t) t.scrollIntoView({ block: 'start' }); };
      toc.append(b);
    }
    head.append(toc);
    el.append(head);
    const body = mk('article', 'tt-lbody');
    for (const s of secs) render(s.md, body, { anchor: 'sec-' + s.id });
    el.append(body);
    if (p.lsec) { const t = document.getElementById('sec-' + p.lsec); if (t) requestAnimationFrame(() => t.scrollIntoView({ block: 'start' })); }
  });
})();
