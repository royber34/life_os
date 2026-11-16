(() => {
  // Evidence trails (client mode): from a key finding to the facts it rests on, each with its source,
  // the quoted passage a checker found there, and the reasoning that joins them. Opens from a card's
  // "How we got here" link or from #trail=<id> in the address, which is what the one-pager links to.
  const T = window.tt;
  const { B, mk } = T;
  const TRAILS = B.trails || {};
  const STATUS = {
    confirmed: 'Confirmed against the source', partly: 'Partly confirmed', unchecked: 'Not checked yet',
    unsupported: 'Not found in the source', wrong: 'Corrected', unreachable: 'Source could not be opened',
  };
  const safe = (url) => (/^https?:\/\//i.test(String(url || '')) ? String(url) : null);
  let dlg = null;

  const sentences = (text) => String(text || '').split(/(?<=[.!?])\s+(?=[A-Z])/).filter(Boolean);

  const open = (id) => {
    const t = TRAILS[id];
    if (!t) return;
    if (!dlg) {
      dlg = mk('dialog', 'tt-trail');
      dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
      dlg.addEventListener('close', () => {
        if (location.hash.startsWith('#trail=')) history.replaceState(null, '', location.pathname + location.search);
      });
      document.body.append(dlg);
    }
    dlg.replaceChildren();
    const head = mk('div', 'tt-trail-head');
    head.append(mk('span', 'tt-plain-label', 'How we got here'));
    const close = mk('button', 'tt-trail-close', 'Close');
    close.onclick = () => dlg.close();
    head.append(close);
    dlg.append(head);
    const title = mk('h2', 'tt-trail-title');
    if (t.value) title.append(mk('span', 'tt-trail-value', t.value), document.createTextNode(' '));
    title.append(document.createTextNode(t.title || ''));
    dlg.append(title);

    if (t.reasoning) {
      const r = mk('section', 'tt-trail-sec');
      r.append(mk('h3', null, 'The reasoning'));
      for (const s of sentences(t.reasoning)) {
        const inf = /^Inference:\s*/i.test(s);
        const p = mk('p', inf ? 'tt-trail-step is-inference' : 'tt-trail-step');
        if (inf) p.append(mk('span', 'tt-tag', 'Inference'), document.createTextNode(' '));
        const body = mk('span');
        const plain = s.replace(/^Inference:\s*/i, '');
        T.md(inf ? plain.charAt(0).toUpperCase() + plain.slice(1) : plain, body);
        p.append(body);
        r.append(p);
      }
      dlg.append(r);
    }

    const c = mk('section', 'tt-trail-sec');
    c.append(mk('h3', null, `The facts it rests on (${(t.claims || []).length})`));
    const list = mk('ol', 'tt-trail-claims');
    for (const x of t.claims || []) {
      const li = mk('li', `tt-trail-claim is-${x.status || 'unchecked'}`);
      li.append(mk('p', 'tt-trail-text', x.text || x.id));
      if (x.quote) li.append(mk('blockquote', 'tt-trail-quote', `"${x.quote}"`));
      const meta = mk('p', 'tt-trail-meta');
      meta.append(mk('span', 'tt-tag', STATUS[x.status] || x.status || 'Not checked yet'));
      if (x.confirmations > 1) meta.append(document.createTextNode(` Checked ${x.confirmations} times.`));
      if (x.basis === 'inference') meta.append(document.createTextNode(' Inference from the sources.'));
      if (x.read) meta.append(document.createTextNode(` Read ${x.read}.`));
      const url = safe(x.checked_url) || safe(x.source);
      if (url) {
        const a = mk('a', 'tt-trail-src', 'Open the source');
        a.href = url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        meta.append(document.createTextNode(' '), a);
      }
      li.append(meta);
      list.append(li);
    }
    c.append(list);
    dlg.append(c);
    dlg.append(mk('p', 'tt-trail-note', 'Every fact comes from a public source, and was checked against it by a separate reviewer who saw only the fact and the source.'));
    if (!dlg.open) dlg.showModal();
    history.replaceState(null, '', `#trail=${encodeURIComponent(id)}`);
  };

  T.openTrail = open;
  const fromHash = () => {
    const m = location.hash.match(/^#trail=(.+)$/);
    if (m) open(decodeURIComponent(m[1]));
  };
  window.addEventListener('hashchange', fromHash);
  window.addEventListener('load', () => setTimeout(fromHash, 200));
})();
