# Battery Monitor (HACS)

Rileva da solo le batterie di Home Assistant, le elenca, notifica quando scendono sotto soglia (% e/o mV) e genera eventi.

## Installazione
HACS → Repository personalizzati → `https://github.com/gerrypc72/panagerry` (categoria *Integrazione*) → installa → riavvia → Impostazioni → Dispositivi e servizi → Aggiungi integrazione → **Battery Monitor**.

## Cosa rileva
- `sensor` con `device_class: battery` (%)
- `binary_sensor` con `device_class: battery` (`on` = scarica)
- `sensor` con `device_class: voltage` il cui entity_id contiene `batter`/`vbat` (V o mV, convertiti in mV)

Le entità dello stesso dispositivo vengono unite in una sola batteria.

## Opzioni
Soglia % (default 20, "sotto"), soglia mV (0 = disattivata), ripetizione notifica in ore (0 = mai), notifica persistente, servizi `notify.*`, entità escluse. Modificabili da *Configura*.

## Sensori
- `sensor.battery_monitor_batteries`: numero di batterie, attributo `batteries` con l'elenco (ordinato per carica)
- `sensor.battery_monitor_low_batteries`: numero di batterie scariche, stesso formato

## Eventi
- `battery_monitor_low`: al passaggio sotto soglia (e a ogni ripetizione, `repeat: true`)
- `battery_monitor_recovered`: quando torna sopra soglia

Dati evento: `name`, `entity_id`, `device_id`, `level`, `voltage_mv`, `reasons` (`percent`/`voltage`/`binary`), `threshold_pct`, `threshold_mv`, `repeat`.

```yaml
automation:
  - trigger:
      - platform: event
        event_type: battery_monitor_low
    action:
      - service: notify.mobile_app_telefono
        data:
          message: "{{ trigger.event.data.name }}: {{ trigger.event.data.level }}%"
```

Servizio `battery_monitor.rescan`: rileva di nuovo le entità (avviene comunque in automatico alla comparsa di nuove entità).
