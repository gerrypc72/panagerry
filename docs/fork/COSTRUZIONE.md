# Panagerry: informazioni di costruzione

Fork personale di [Panalume](https://github.com/leacho73/panalume) (licenza MIT, il file `LICENSE` con il copyright originale va mantenuto).
Dashboard drag-and-drop per Home Assistant, installata come add-on locale accanto all'originale.

- Repo del fork: `gerrypc72/panagerry`, branch `main`. Remote `origin`.
- Repo originale: `leacho73/panalume`, remote `upstream` (da aggiungere in un clone nuovo, vedi AGGIORNAMENTI.md).
- Base di partenza: Panalume **0.38.0**, commit upstream `7417084`.
- Stack: Svelte 5 + Vite 8, server Node (`app/server/index.js`), add-on HA con `Dockerfile` (node:22-alpine, `npm ci` + `npm run build` dentro il container).

## Struttura utile

```
panalume/                 cartella dell'add-on (config.yaml, Dockerfile, DOCS.md, CHANGELOG.md)
  config.yaml             nome, slug, versione: la versione va aumentata a ogni rilascio
  app/
    src/cards/            una carta = un file .svelte (registrate in automatico da lib/registry.js)
    src/lib/config.svelte.js   modello della dashboard (viste, layout, schermi di destinazione)
    src/components/Stage.svelte  canvas e scala; Editor.svelte  pannelli di modifica
    server/index.js       server (config in DATA_DIR/dashboard.json, proxy verso HA)
repository.yaml           intestazione del repo di add-on
docs/fork/                questi documenti
```

## Cosa differisce dall'originale (versioni del fork)

| Versione | Modifica | File principali |
|---|---|---|
| 0.38.1 | **Supporto Octopus rimosso.** Eliminate le carte Octopus rates, Octoplus sessions, Intelligent Octopus, Energy cost today, Heat pump. Tolto l'auto-rilevamento Octopus da Energy usage, EV, Climate group, vista Energy automatica. Zappi/Eddi: tolto il tracker delle ore economiche. `lib/octopus.js` rinominato `lib/util.js`, ridotto a `find`, `hm`, `day`, `until` e helper myenergi. | `cards/` (5 file eliminati), `Myenergi.svelte`, `lib/util.js`, `lib/fusion.js` |
| 0.38.2 | **Layout unico.** `detectDevice()` restituisce sempre `'tablet'`; `otherLayouts()` restituisce `[]`; tolti il selettore dispositivo (App.svelte) e le sezioni Devices / New cards / Copy to layout (Editor.svelte). I layout phone e desktop restano nei dati ma non vengono mostrati. | `lib/config.svelte.js`, `App.svelte`, `components/Editor.svelte` |
| 0.38.2 | **Carta Linear gauge** (`gauge-linear`) e **carta Wind rose** (`windrose`, pensata per Ecowitt). | `cards/LinearGauge.svelte`, `cards/WindRose.svelte` |
| 0.38.3 | **Schermo di destinazione per board.** Ogni vista può avere `width` e `height` propri (preset iPad, Echo Spot / Show 5 / Show 8, custom). `layout()` restituisce un layout con quella larghezza/altezza e senza sidebar (`baseLayout()` è l'originale). Stage: display `screen` forzato, niente "fill", cornice tratteggiata in modifica. Pulsante **Duplicate** per copiare una board con carte indipendenti. | `lib/config.svelte.js` (`SCREENS`, `screenKey`, `setViewScreen`, `duplicateView`), `Stage.svelte`, `Editor.svelte` |
| 0.38.4 | **Add-on rinominato Panagerry** (slug `panagerry`, titolo, icona `mdi:compass-rose`, URL e maintainer in `repository.yaml`), per convivere con Panalume. | `config.yaml`, `repository.yaml` |
| 0.38.5 | **Nuova icona e logo** (rosa dei venti, sfumatura turchese-ambra) per distinguere Panagerry da Panalume. Immagini generate con uno script Pillow (non nel repo): `panalume/icon.png` 128×128, `panalume/logo.png` 250×100. | `panalume/icon.png`, `panalume/logo.png`, `README.md` |

## Build in locale (Mac)

Requisiti: **Node 22.12 o superiore** (Vite 8). Il Mac Intel (i7) ha richiesto una correzione per `rolldown`.

```bash
cd panalume/app
npm ci
npm run build
```

Se `npm run build` fallisce con `Cannot find native binding` (bug npm sulle dipendenze opzionali): aggiorna Node (≥22.12),
poi `rm -rf node_modules && npm ci`; se serve, `npm install --no-save @rolldown/binding-darwin-x64@<versione di rolldown>`
(`--no-save`: non modifica `package.json` né il lockfile). Non committare un lockfile rigenerato senza motivo: il `Dockerfile`
usa `npm ci` e il lockfile attuale contiene i moduli nativi per Linux (anche `linux-arm64-musl`, quello dell'RPi5).
L'avviso "Some chunks are larger than 500 kB" è normale, si ignora.

## Prova in locale con HA vero

```bash
echo "TOKEN_UTENTE_HA" > /tmp/ha_token.txt          # fuori dal repo, mai committato
cd panalume/app
HA_URL=http://<IP-DI-HA>:8123 HA_TOKEN_FILE=/tmp/ha_token.txt npm run server   # :8099
npm run dev                                                                      # Vite su :5173
```
- La dashboard di prova resta in `panalume/app/data/dashboard.json` (ignorato da git): non tocca quella dell'add-on in HA.
- Il token comanda HA: i pulsanti sulle carte eseguono azioni vere. Cancella `/tmp/ha_token.txt` a fine prova.

## Installazione in HA come add-on locale

Se il repo è **privato**, HA non può leggerlo dall'elenco dei repository di add-on (servirebbe un token nell'URL): si copia la cartella come add-on locale (sotto). Se il repo è **pubblico**, si può aggiungere come repository (Impostazioni → App → Store → ⋮ → Repository → `https://github.com/gerrypc72/panagerry`): l'add-on risulta allora un'istanza diversa da quella locale (`<hash>_panagerry` invece di `local_panagerry`) con una cartella dati propria, quindi esporta/copia la dashboard prima di passare dall'una all'altra e non tenere installate entrambe.

1. In HA: componente **Samba share** (o SSH) con le cartelle condivise.
2. Mac: Finder → Connetti al server → `smb://<IP-DI-HA>/addons` (monta `/Volumes/addons`).
3. Copia, escludendo i file di build del Mac (`config.yaml` e `Dockerfile` devono stare direttamente in `addons/panagerry/`):
   ```bash
   cd panalume
   rsync -av --exclude node_modules --exclude dist --exclude data ./ /Volumes/addons/panagerry/
   ```
4. HA → **Impostazioni → App** (ex Componenti aggiuntivi) → store → **Controlla aggiornamenti**; oppure da terminale SSH `ha store reload`.
   In fondo compare la sezione di app locali con **Panagerry**: Installa (la costruzione sull'RPi5 richiede qualche minuto), Avvia,
   attiva "Mostra nella barra laterale".
- Se la voce non compare, copia anche in `local_apps/panagerry` (nelle versioni recenti esistono sia `addons` sia `local_apps`).
- Dati separati da Panalume: ogni add-on ha la propria `/data`. Le dashboard dell'uno non appaiono nell'altro.
- Tutto questo è stato provato e funziona (build Mac, prova in locale, installazione in HA). Il comportamento delle singole carte nuove
  su dati reali Ecowitt non è stato verificato.

## Accesso da browser

1. **Tramite Home Assistant** (con il login di HA): voce **Panagerry** nella barra laterale, oppure
   `http://<IP-DI-HA>:8123/local_panagerry` per l'add-on locale (per l'add-on installato da repository il prefisso `local_` è
   un codice, visibile nell'indirizzo quando si apre dalla barra laterale). I parametri funzionano:
   `…/local_panagerry?kiosk&fit=screen#NOME_BOARD`.
2. **Porta diretta** (senza login HA, per i device a muro): disattivata di default. Pagina dell'add-on → Configurazione → Rete →
   assegna una porta a `8099/tcp` (es. **8100**, diversa da quella di Panalume se ce l'ha), salva e riavvia l'add-on.
   Indirizzo: `http://<IP-DI-HA>:8100/?fit=screen#NOME_BOARD`.
   **Sicurezza:** chiunque sia sulla rete raggiunge la dashboard senza password e, tramite il permesso dell'add-on verso HA,
   può comandare entità e servizi. Solo su rete di casa fidata, mai esposta a internet (niente port forwarding).

## Stato e limiti noti

- **Wind rose:** l'auto-rilevamento cerca sensori `*_wind_direction`, `*_wind_speed`, `*_wind_gust`, `*_max_daily_gust`.
  I nomi esatti del tuo Ecowitt non erano noti: correggi a mano le entità se non vengono trovate.
- **Preset schermo:** le dimensioni degli Echo sono i pixel fisici; il browser può vedere pixel CSS diversi (densità). Misura sul device
  (il pannello Layout mostra "This screen: W×H") e usa "Custom size". I preset iPad sono approssimati.
- **Cambio dimensione di una board:** le carte non vengono ridimensionate, restano dove sono.
- **Dashboard esistenti** con carte Octopus rimosse mostrano carte sconosciute: vanno cancellate dall'editor.
- **Tag git:** i 36 tag dell'originale non sono stati copiati (il push dei tag è fallito) e il branch `docker` dell'originale non c'è.
- **GitHub Actions:** `.github/workflows/release.yml` parte a ogni push su `main` e può creare release/tag nel fork. Valuta di disattivarlo.
