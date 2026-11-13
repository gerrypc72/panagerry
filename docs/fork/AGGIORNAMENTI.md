# Panagerry: aggiornamenti

Due casi: (A) modifiche tue al fork, (B) portare dentro gli aggiornamenti di Panalume (`upstream`).

## A. Rilasciare una modifica tua

1. Modifica il codice in `panalume/app/src/`.
2. Verifica: `cd panalume/app && npm run build` (e, per prove con HA vero, `npm run server` + `npm run dev`, vedi COSTRUZIONE.md).
3. **Aumenta la versione** in `panalume/config.yaml` (`version: "0.38.x"`) e aggiungi una voce in cima a `panalume/CHANGELOG.md`.
   Senza cambio di versione HA non propone "Aggiorna".
4. Commit e push su `main`:
   ```bash
   git add -A && git commit -m "descrizione" && git push
   ```
5. Copia l'add-on in HA (con la condivisione `addons` montata):
   ```bash
   cd panalume
   rsync -av --exclude node_modules --exclude dist --exclude data ./ /Volumes/addons/panagerry/
   ```
6. In HA: **Impostazioni → App → Panagerry** → **Aggiorna** (se la versione è cambiata) oppure **Ricostruisci**. Se lo store non vede la novità: `ha store reload` da terminale SSH.
   I dati (dashboard) restano: stanno in `/data` dell'add-on e non vengono toccati dall'aggiornamento.

Regole pratiche: modifiche piccole e una alla volta; niente token nel repo; non rigenerare `package-lock.json` senza motivo.

## B. Portare dentro gli aggiornamenti di Panalume

Nel clone locale, una volta sola:
```bash
git remote add upstream https://github.com/leacho73/panalume.git
```
Poi:
```bash
git fetch upstream
git log --oneline HEAD..upstream/main      # cosa c'è di nuovo
git merge upstream/main
```
Prima di fare il merge leggi il CHANGELOG upstream: se le novità non ti servono, puoi anche non farlo.

**Conflitti prevedibili e come risolverli**

| Dove | Perché | Come |
|---|---|---|
| `cards/OctopusRates`, `OctopusSessions`, `OctopusIntelligent`, `HeatPump`, `EnergyToday` | eliminati nel fork | se upstream li modifica: `git rm` (tenere eliminati) |
| `lib/octopus.js` | nel fork è `lib/util.js`, ridotto | se upstream cambia helper generici (`find`, `hm`, `day`, `until`, myenergi), riporta la modifica a mano in `util.js` |
| `Myenergi.svelte`, `EnergyUsage.svelte`, `EV.svelte`, `ClimateGroup.svelte`, `lib/fusion.js` | tolto il codice Octopus | tieni la versione del fork, ricontrolla poi con `grep -rni octopus panalume/app/src` |
| `lib/config.svelte.js` | `detectDevice`, `otherLayouts`, `layout()`/`baseLayout()`, `SCREENS`, `screenKey`, `setViewScreen`, `duplicateView` | unisci a mano, tenendo le funzioni del fork |
| `components/Stage.svelte` | `display`, `mainContentH`, `fill`, cornice `.frame` | unisci a mano |
| `components/Editor.svelte`, `App.svelte` | pannello Layout semplificato, campi schermo/Duplicate nel pannello Views, selettore dispositivo tolto | unisci a mano |
| `config.yaml` | upstream (da 0.40.0) ha la riga `image: "ghcr.io/leacho73/{arch}-panalume"` | **non prenderla mai**: con `image:` HA scarica l'immagine di upstream e ignora il tuo codice. Tieni nome, slug, URL, icona del fork e nessuna riga `image:` |
| `panalume/Dockerfile` | upstream usa `FROM --platform=$BUILDPLATFORM` e le etichette di Panalume | tieni `FROM node:22-alpine AS build` (la costruzione avviene in HA) e le etichette Panagerry |
| `app/vite.config.js` | il fork ha `cssTarget: ['chrome61', 'safari14']` | tienilo: senza, le carte tornano bianche e vuote sugli Echo Show. Dopo ogni merge verifica che ci sia ancora, e riprova sul Show |
| `.github/workflows/release.yml` | pubblica immagini su ghcr.io e crea release | tieni `if: github.repository == 'leacho73/panalume'` sui job `image` e `release` |
| `config.yaml`, `repository.yaml`, `CHANGELOG.md` | nome, slug, URL, icona, versione del fork | tieni nome/slug/URL/icona del fork; versione = la tua successiva |

Dopo il merge:
1. `grep -rni octopus panalume/app/src` deve restare vuoto (a parte il CHANGELOG storico).
2. `cd panalume/app && npm ci && npm run build`.
3. Aumenta la versione, aggiorna il CHANGELOG, poi segui il punto A dal passo 4.
4. Controlla in locale (`npm run dev`) le carte Linear gauge, Wind rose, il campo schermo di una board e Duplicate.

## Cose da tenere d'occhio

- **Rinomina dell'add-on:** `slug: panagerry` non va cambiato, altrimenti HA lo tratta come un add-on nuovo (dati inclusi).
- **Se il repo è pubblico e l'add-on è installato da repository:** dopo il push su `main` con la versione aumentata, in HA basta Controlla aggiornamenti (o `ha store reload`) e Aggiorna; il passo `rsync` non serve. Se lo richiudi privato, HA non vede più le novità finché non lo riapri.
- **Repo privato e HA:** l'installazione da elenco repository richiederebbe un token nell'URL; per questo si usa la copia in `addons/`.
- **Sincronizzazione repo:** in `HAVoiceLab` lo script `sync.sh` include anche `panagerry` (cartella sorella `~/voice/panagerry`).
- **Segreti:** nessun token nel repo; le prove usano `/tmp/ha_token.txt` fuori dal repo.
