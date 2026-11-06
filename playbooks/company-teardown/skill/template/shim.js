// Small runtime: bundle access, one params object, explicit defaults, and tab-gated drawing.
window.dash = (() => {
  const bundle = JSON.parse(document.getElementById('bundle').textContent);
  const colors = [1, 2, 3, 4, 5, 6, 7, 8].map((i) => `var(--cds-chart-${i})`);
  const draws = new Map();
  const dataCbs = [];
  let defaults = {};
  let params = {};
  let pending = false;
  let drawCount = 0;

  const clone = (v) => (Array.isArray(v) ? v.slice() : v);
  const rows = (id) => {
    if (id === 'supply' || id === 'demand') return (bundle.config.market && bundle.config.market[id]) || [];
    return bundle[id] || [];
  };

  const drawEl = (el) => {
    const fn = draws.get(el.dataset.draw);
    if (!fn) throw new Error(`No draw function named ${el.dataset.draw}`);
    try {
      fn(el);
      drawCount += 1;
    } catch (err) {
      console.error(`Draw failed: ${el.dataset.draw}`, err);
      const box = document.createElement('div');
      box.className = 'tt-missing';
      box.textContent = `Failed to draw ${el.dataset.draw}: ${err.message}`;
      if (el.tagName !== 'SELECT' && el.tagName !== 'TBODY') el.replaceChildren(box);
    }
  };

  // Only the visible tab draws. A chart in a hidden page would read a width of zero.
  const flush = () => {
    pending = false;
    for (const cb of dataCbs) cb();
    for (const el of document.querySelectorAll('[data-draw]')) {
      if (!el.closest('[hidden]')) drawEl(el);
    }
  };
  const schedule = () => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(flush);
  };

  let resizeTimer;
  let lastWidth = window.innerWidth;
  window.addEventListener('resize', () => {
    if (window.innerWidth === lastWidth) return;
    lastWidth = window.innerWidth;
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(schedule, 150);
  });

  return {
    bundle,
    colors,
    rows,
    params: () => params,
    defaults: () => defaults,
    setDefaults: (d) => {
      defaults = d;
      params = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, clone(v)]));
    },
    setParams: (patch) => {
      params = { ...params, ...patch };
      schedule();
    },
    resetParams: (keep = []) => {
      const held = Object.fromEntries(keep.map((k) => [k, params[k]]));
      params = { ...Object.fromEntries(Object.entries(defaults).map(([k, v]) => [k, clone(v)])), ...held };
      schedule();
    },
    draw: (name, fn) => draws.set(name, fn),
    onData: (fn) => dataCbs.push(fn),
    setLink: (hash) => {
      try { history.replaceState(null, '', `#${hash}`); } catch (e) { location.hash = hash; }
    },
    start: schedule,
    drawCount: () => drawCount,
  };
})();
