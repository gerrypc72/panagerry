// Small shared helpers: entity lookup, time formatting and myenergi power sensors.
import { states } from './ha.svelte.js';

/** First entity id matching the regex (used to auto-fill new cards). */
export function find(re) {
  for (const id of states.keys()) if (re.test(id)) return id;
  return '';
}

export function until(t, now) {
  const m = Math.round((t - now) / 60000);
  if (Math.abs(m) < 60) return `${m}m`;
  const h = Math.floor(Math.abs(m) / 60), r = Math.abs(m) % 60;
  if (h < 24) return `${h}h${r ? ' ' + r + 'm' : ''}`;
  return `${Math.round(h / 24)}d`;
}

export const hm = (t) => new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
export const day = (t, now = Date.now()) => {
  const d = new Date(t), n = new Date(now);
  const diff = Math.round((new Date(d.toDateString()) - new Date(n.toDateString())) / 864e5);
  return diff === 0 ? 'Today' : diff === 1 ? 'Tomorrow' : diff === -1 ? 'Yesterday' : d.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short' });
};

// myenergi: the hub's "power charging" adds up every Zappi and Eddi (e.g. a 7 kW
// car charge plus a 3 kW immersion reads 10 kW). Prefer the device's own reading.
export const HUB_CHARGING = /^sensor\.myenergi_hub_.+_power_charging/;
/** Template listing every Zappi / Eddi's own power sensor (so the dashboard can watch them). */
export const MYENERGI_OWN = "{{ states.sensor | map(attribute='entity_id') | select('match', 'sensor[.]myenergi_(zappi|eddi)_[0-9]+_power_ct_internal_load$') | join(',') }}";
export function myenergiPower(id, device = 'zappi', hint = '') {
  if (!id || !HUB_CHARGING.test(id)) return id;
  const serial = String(hint).match(new RegExp(`myenergi_${device}_(\\d+)`))?.[1];
  const own = [...states.keys()].find((k) => new RegExp(`^sensor\\.myenergi_${device}_${serial || '\\d+'}_power_ct_internal_load$`).test(k));
  return own || id;
}
