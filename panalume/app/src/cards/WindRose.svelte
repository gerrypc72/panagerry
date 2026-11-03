<script module>
  import { find } from '../lib/util.js';
  export const meta = {
    type: 'windrose', name: 'Wind rose', icon: 'mdi:compass-rose', category: 'Info',
    size: { w: 280, h: 300 }, tap: 'more-info',
    infoEntity: (p) => p.direction || p.speed,
    defaults: { arrow: 'to', lang: 'it' },
    // Entity names of the Ecowitt integration; anything else can be picked by hand.
    autofill: () => ({
      direction: find(/^sensor\..*wind_dir(ection)?$/),
      speed: find(/^sensor\..*wind_speed$/),
      gust: find(/^sensor\..*wind_gust$/),
      gust_max: find(/^sensor\..*(max_daily_gust|daily_max_gust|gust_max.*)$/),
    }),
    fields: [
      { key: 'name', label: 'Name', type: 'text' },
      { key: 'direction', label: 'Wind direction (degrees, where it blows from)', type: 'entity', domain: 'sensor' },
      { key: 'speed', label: 'Wind speed', type: 'entity', domain: 'sensor' },
      { key: 'gust', label: 'Gust', type: 'entity', domain: 'sensor' },
      { key: 'gust_max', label: 'Max gust today (optional)', type: 'entity', domain: 'sensor' },
      { key: 'avg_dir', label: 'Average direction (optional, drawn as a ring marker)', type: 'entity', domain: 'sensor' },
      { key: 'arrow', label: 'Arrow', type: 'select', options: [{ value: 'to', label: 'Points where the wind blows' }, { value: 'from', label: 'Points to where it comes from' }] },
      { key: 'lang', label: 'Compass letters', type: 'select', options: [{ value: 'it', label: 'Italiano (N E S O)' }, { value: 'en', label: 'English (N E S W)' }] },
    ],
  };
</script>

<script>
  import { untrack } from 'svelte';
  import { t, ent } from '../lib/tpl.js';
  import { formatNumber, stateText } from '../lib/entity.js';
  let { props } = $props();
  const NAMES = {
    en: ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'],
    it: ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSO', 'SO', 'OSO', 'O', 'ONO', 'NO', 'NNO'],
  };
  const names = $derived(NAMES[props.lang === 'en' ? 'en' : 'it']);
  const dirE = $derived(ent(props.direction));
  const speedE = $derived(ent(props.speed));
  const gustE = $derived(ent(props.gust));
  const maxE = $derived(ent(props.gust_max));
  const deg = $derived(Number(dirE?.state));
  const avg = $derived(Number(ent(props.avg_dir)?.state));
  const ok = $derived(Number.isFinite(deg));
  const cardinal = $derived(ok ? names[Math.round((((deg % 360) + 360) % 360) / 22.5) % 16] : '—');
  // The needle turns the short way round (359° → 1° doesn't spin the whole circle).
  let shown = $state(0);
  $effect(() => {
    if (!ok) return;
    const target = deg;
    const cur = untrack(() => shown);
    shown = cur + ((((target - cur) % 360) + 540) % 360) - 180;
  });
  const needle = $derived(shown + (props.arrow === 'from' ? 0 : 180));
  const ticks = Array.from({ length: 72 }, (_, i) => i * 5);
  const labelAt = (i) => {
    const a = ((i * 22.5) * Math.PI) / 180;
    const r = i % 4 === 0 ? 76 : 0;
    return { x: Math.sin(a) * r, y: -Math.cos(a) * r };
  };
</script>

<div class="rose">
  <svg viewBox="-100 -100 200 200">
    <circle r="92" class="ring" />
    {#each ticks as a}
      <line x1="0" y1={a % 90 === 0 ? -92 : a % 45 === 0 ? -88 : -90} x2="0" y2="-95" class="tick" class:major={a % 45 === 0} transform="rotate({a})" />
    {/each}
    {#each [0, 4, 8, 12] as i}
      <text x={labelAt(i).x} y={labelAt(i).y} class="cd" class:north={i === 0} text-anchor="middle" dominant-baseline="central">{names[i]}</text>
    {/each}
    {#each [2, 6, 10, 14] as i}
      {@const a = (i * 22.5 * Math.PI) / 180}
      <text x={Math.sin(a) * 76} y={-Math.cos(a) * 76} class="ic" text-anchor="middle" dominant-baseline="central">{names[i]}</text>
    {/each}
    {#if Number.isFinite(avg)}
      <circle cx="0" cy="-92" r="4.5" class="avg" transform="rotate({avg})" />
    {/if}
    {#if ok}
      <g class="needle" style="transform: rotate({needle}deg)">
        <polygon points="0,-58 9,-34 3,-34 3,40 -3,40 -3,-34 -9,-34" />
      </g>
    {/if}
    <circle r="22" class="hub" />
    <text y="-2" class="spd" text-anchor="middle" dominant-baseline="central">{speedE && Number.isFinite(Number(speedE.state)) ? formatNumber(Number(speedE.state)) : '—'}</text>
    <text y="11" class="unit" text-anchor="middle" dominant-baseline="central">{speedE?.attributes.unit_of_measurement || ''}</text>
  </svg>
  <div class="info">
    <b>{t(props.name) || ''}{#if t(props.name)}{' · '}{/if}{ok ? `${cardinal} ${Math.round(deg)}°` : '—'}</b>
    {#if gustE}<span>{props.lang === 'en' ? 'Gust' : 'Raffica'} {stateText(gustE)}</span>{/if}
    {#if maxE}<span>{props.lang === 'en' ? 'Max today' : 'Max oggi'} {stateText(maxE)}</span>{/if}
  </div>
</div>

<style>
  .rose { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; }
  svg { flex: 1 1 auto; min-height: 0; width: 100%; max-height: 100%; }
  .ring { fill: rgba(255,255,255,.04); stroke: rgba(255,255,255,.12); stroke-width: 1; }
  .tick { stroke: rgba(255,255,255,.28); stroke-width: 1; }
  .tick.major { stroke: rgba(255,255,255,.6); stroke-width: 1.6; }
  .cd { fill: var(--text); font-size: 13px; font-weight: 700; }
  .cd.north { fill: #ff6b6b; }
  .ic { fill: var(--muted); font-size: 8px; }
  .needle { transform-origin: 0 0; transition: transform .8s cubic-bezier(.3,.7,.3,1); fill: var(--accent); }
  .hub { fill: rgba(11,15,23,.85); stroke: rgba(255,255,255,.2); stroke-width: 1; }
  .spd { fill: var(--text); font-size: 15px; font-weight: 700; }
  .unit { fill: var(--muted); font-size: 7px; }
  .avg { fill: none; stroke: var(--on); stroke-width: 2; }
  .info { display: flex; flex-direction: column; align-items: center; font-size: .9em; line-height: 1.3; }
  .info span { color: var(--muted); font-size: .9em; }
</style>
