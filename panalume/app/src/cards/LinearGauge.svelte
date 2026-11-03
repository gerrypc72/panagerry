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
  const color = $derived.by(() => {
    if (props.color) return t(props.color);
    const r = num('red'), y = num('yellow'), g = num('green');
    if (r != null && v >= r) return '#ff6b6b';
    if (y != null && v >= y) return '#ffc861';
    if (g != null && v >= g) return '#5bd88f';
    return 'var(--accent)';
  });
  const vertical = $derived(props.orientation === 'vertical');
  const unit = $derived(t(props.unit) || e?.attributes.unit_of_measurement || '');
  const label = $derived(t(props.name) || name(e));
</script>

<div class="lg" class:vertical>
  <div class="head">
    <span class="name">{label}</span>
    <span class="val">{Number.isNaN(v) ? '—' : formatNumber(v)}<small>{unit}</small></span>
  </div>
  <div class="body">
    <div class="track"><div class="fill" style="{vertical ? 'height' : 'width'}:{f * 100}%;background:{color}"></div></div>
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
  .track { height: 12px; border-radius: 6px; background: rgba(255,255,255,.1); overflow: hidden; display: flex; }
  .fill { height: 100%; border-radius: 6px; transition: width .6s, height .6s, background .3s; }
  .scale { display: flex; justify-content: space-between; color: var(--muted); font-size: .75em; }
  /* vertical: the bar grows upward and fills the card */
  .vertical { flex-direction: column; justify-content: flex-start; }
  .vertical .body { flex: 1; min-height: 0; flex-direction: row-reverse; justify-content: center; gap: 8px; }
  .vertical .track { width: 14px; height: 100%; flex-direction: column; justify-content: flex-end; }
  .vertical .fill { width: 100%; }
  .vertical .scale { flex-direction: column-reverse; align-items: flex-start; }
</style>
