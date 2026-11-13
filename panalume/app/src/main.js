import './lib/compat.js';
import { mount } from 'svelte';
import './inter.css';
import './app.css';
import App from './App.svelte';
import { param } from './lib/params.js';

mount(App, { target: document.getElementById('app') });

// ?diag: on-screen rendering diagnostics for a device that draws the dashboard wrongly (tap to close).
if (param('diag') !== null) import('./lib/diag.js').then((m) => setTimeout(m.runDiag, 3000));
