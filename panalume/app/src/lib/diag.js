// On-screen diagnostics for a device whose rendering looks wrong (open the page with ?diag).
// Shows how this browser engine treats the colour syntaxes the stylesheet uses and how it
// parsed the real rules of the Fan card, so no remote debugging is needed.
export function runDiag() {
  const out = [];
  const log = (s) => out.push(s);
  const safe = (label, fn) => { try { log(`${label}: ${fn()}`); } catch (e) { log(`${label}: ERROR ${e.message}`); } };
  const sup = (prop, val) => (CSS.supports(prop, val) ? 'yes' : 'NO');

  safe('UA', () => navigator.userAgent);
  safe('screen', () => `${innerWidth}x${innerHeight} dpr ${devicePixelRatio}`);
  safe('supports rgba(255,255,255,.06)', () => sup('background-color', 'rgba(255,255,255,.06)'));
  safe('supports #ffffff0f (hex8)', () => sup('background-color', '#ffffff0f'));
  safe('supports rgb(255 255 255 / 6%)', () => sup('background-color', 'rgb(255 255 255 / 6%)'));
  safe('supports color-mix()', () => sup('background-color', 'color-mix(in srgb, red 50%, blue)'));
  safe('supports inset / aspect-ratio / :is()', () => `${sup('inset', '0')} / ${sup('aspect-ratio', '1/1')} / ${CSS.supports('selector(:is(a))') ? 'yes' : 'NO'}`);

  // What the engine makes of each syntax when it's set on a real element.
  const probe = document.createElement('div');
  probe.style.cssText = 'position:fixed;left:-9999px;top:0;width:10px;height:10px';
  document.body.appendChild(probe);
  for (const v of ['rgba(255,255,255,.06)', '#ffffff0f', 'rgb(255 255 255 / 6%)', 'rgba(91,216,143,.22)']) {
    safe(`computed bg for ${v}`, () => { probe.style.background = 'none'; probe.style.background = v; return getComputedStyle(probe).backgroundColor || '(empty)'; });
  }
  probe.remove();

  // How the engine parsed the real, minified rules shipped in the stylesheet.
  const want = ['.pw', '.chip', '.ic', '.slider'];
  const seen = {};
  const walk = (rules) => {
    for (const r of rules || []) {
      if (r.cssRules && !r.selectorText) { walk(r.cssRules); continue; }
      const sel = r.selectorText || '';
      for (const w of want) {
        if (seen[w] || !new RegExp('(^|[ ,>])' + w.replace('.', '\\.') + '(\\.|\\s|,|$|:)').test(sel)) continue;
        if (!/background|border-radius/.test(r.cssText)) continue;
        seen[w] = true;
        log(`rule ${sel.slice(0, 40)} → bg="${r.style.getPropertyValue('background') || r.style.getPropertyValue('background-color') || '(none)'}"`);
        log(`   cssText: ${r.cssText.slice(0, 200)}`);
      }
    }
  };
  safe('stylesheets', () => {
    let n = 0;
    for (const s of document.styleSheets) { try { n += s.cssRules.length; walk(s.cssRules); } catch {} }
    return `${n} rules`;
  });

  // The live elements, if a Fan card is on this view.
  for (const sel of ['.fan .pw', '.fan .chip', '.fan .ic', '.fan .slider']) {
    safe(`live ${sel}`, () => {
      const el = document.querySelector(sel);
      if (!el) return 'not on this view';
      const cs = getComputedStyle(el);
      return `bg ${cs.backgroundColor} | radius ${cs.borderRadius} | ${Math.round(el.getBoundingClientRect().width)}x${Math.round(el.getBoundingClientRect().height)}`;
    });
  }

  const box = document.createElement('pre');
  box.textContent = out.join('\n');
  box.style.cssText = 'position:fixed;inset:0;z-index:2147483647;margin:0;padding:12px;overflow:auto;background:#000;color:#0f0;font:12px/1.35 monospace;white-space:pre-wrap;word-break:break-all';
  box.onclick = () => box.remove();
  document.body.appendChild(box);
}
