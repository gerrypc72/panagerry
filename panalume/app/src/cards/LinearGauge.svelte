<script module>
  export const meta = {
    type: 'gauge-linear', name: 'Linear gauge', icon: 'mdi:gauge-low', category: 'Info',
    size: { w: 320, h: 100 }, tap: 'more-info',
    defaults: { entity: '', min: 0, max: 100, orientation: 'horizontal', scale: true },
    fields: [
      { key: 'entity', label: 'Entity', type: 'entity' },
      { key: 'name', label: 'Name', type: 'text' },
      { key: 'value', label: 'Value (override/template)', type: 'text' },
      { key: 'unit', label: 'Unit', type: 'text' },
      { key: 'orientation', label: 'Orientation', type: 'select', options: ['horizontal', 'vertical'] },
      { key: 'min', label: 'Min', type: 'text' },
      { key: 'max', label: 'Max', type: 'text' },
      { key: 'scale', label: 'Show min / max labels', type: 'bool' },
      { key: 'green', label: 'Green from', type: 'text' },
      { key: 'yellow', label: 'Yellow from', type: 'text' },
      { key: 'red', label: 'Red from', type: 'text' },
      { key: 'bands', label: 'Colour bands (instead of green / yellow / red)', type: 'text', placeholder: '0 red, 20 orange, 40 green', hint: 'Each colour applies from its number up to the next one, so low can be red (fuel, battery) and a range can be green in the middle: 0 red, 20 orange, 40 green, 80 orange, 90 red. Names or any CSS colour.' },
      { key: 'bands_track', label: 'Show the bands along the bar', type: 'bool' },
      { key: 'color', label: 'Colour (fixed/template)', type: 'color' },
    ],
  };
</script>

<script>
  import { t, ent } from '../lib/tpl.js';
  import { name, formatNumber } from '../lib/entity.js';
  let { props } = $props();
  const e = $derived(ent(props.entity));
  const v = $derived(Number(props.value ? t(props.value) : e?.state));
  const min = $derived(Number(t(props.min)) || 0);
  const max = $derived(Number(t(props.max)) || 100);
  const f = $derived(Number.isNaN(v) || max === min ? 0 : Math.min(1, Math.max(0, (v - min) / (max - min))));
  const num = (k) => (props[k] === '' || props[k] == null ? null : Number(t(props[k])));
  // The house's own shades for the usual names; anything else is used as given.
  const SHADE = { red: '#ff6b6b', orange: '#ff9a3c', amber: '#ffc861', yellow: '#ffc861', green: '#5bd88f', blue: '#4fb4ff' };
  // "0 red, 20 orange, 40 green" → bands from each number upwards, lowest first.
  const bands = $derived(String(t(props.bands) ?? '').split(',').map((b) => b.trim().match(/^(-?\d+(?:[.,]\d+)?)\s+(.+)$/)).filter(Boolean)
    .map((m) => ({ from: Number(m[1].replace(',', '.')), color: SHADE[m[2].trim().toLowerCase()] || m[2].trim() })).sort((a, b) => a.from - b.from));
  const color = $derived.by(() => {
    if (props.color) return t(props.color);
    if (bands.length) return Number.isNaN(v) ? 'var(--accent)' : [...bands].reverse().find((b) => v >= b.from)?.color || bands[0].color;
    const r = num('red'), y = num('yellow'), g = num('green');
    if (r != null && v >= r) return '#ff6b6b';
    if (y != null && v >= y) return '#ffc861';
    if (g != null && v >= g) return '#5bd88f';
    return 'var(--accent)';
  });
  const vertical = $derived(props.orientation === 'vertical');
  // The bands drawn along the bar, faintly, behind the fill (the lowest band also covers below its number).
  const track = $derived.by(() => {
    if (!props.bands_track || !bands.length || max === min) return '';
    const at = (x) => Math.min(100, Math.max(0, ((x - min) / (max - min)) * 100));
    const stops = bands.map((b, i) => `${b.color} ${i === 0 ? 0 : at(b.from)}% ${i + 1 < bands.length ? at(bands[i + 1].from) : 100}%`);
    return `linear-gradient(${vertical ? 'to top' : 'to right'}, ${stops.join(', ')})`;
  });
  const unit = $derived(t(props.unit) || e?.attributes.unit_of_measurement || '');
  const label = $derived(t(props.name) || name(e));
</script>

<div class="lg" class:vertical>
  <div class="head">
    <span class="name">{label}</span>
    <span class="val">{Number.isNaN(v) ? '—' : formatNumber(v)}<small>{unit}</small></span>
  </div>
  <div class="body">
    <div class="track">{#if track}<div class="bands" style="background:{track}"></div>{/if}<div class="fill" style="{vertical ? 'height' : 'width'}:{f * 100}%;background:{color}"></div></div>
    {#if props.scale !== false}
      <div class="scale"><span>{formatNumber(min)}</span><span>{formatNumber(max)}</span></div>
    {/if}
  </div>
</div>

<style>
  .lg { height: 100%; display: flex; flex-direction: column; justify-content: center; gap: 8px; }
  .head { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .name { color: var(--muted); font-size: .9em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .val { font-size: 1.4em; font-weight: 600; white-space: nowrap; }
  small { font-size: .55em; color: var(--muted); margin-left: 2px; }
  .body { display: flex; flex-direction: column; gap: 4px; }
  .track { position: relative; height: 12px; border-radius: 6px; background: rgba(255,255,255,.1); overflow: hidden; display: flex; }
  .bands { position: absolute; inset: 0; opacity: .35; }
  .fill { position: relative; height: 100%; border-radius: 6px; transition: width .6s, height .6s, background .3s; }
  .scale { display: flex; justify-content: space-between; color: var(--muted); font-size: .75em; }
  /* vertical: the bar grows upward and fills the card */
  .vertical { flex-direction: column; justify-content: flex-start; }
  .vertical .body { flex: 1; min-height: 0; flex-direction: row-reverse; justify-content: center; gap: 8px; }
  .vertical .track { width: 14px; height: 100%; flex-direction: column; justify-content: flex-end; }
  .vertical .fill { width: 100%; }
  .vertical .scale { flex-direction: column-reverse; align-items: flex-start; }
</style>
