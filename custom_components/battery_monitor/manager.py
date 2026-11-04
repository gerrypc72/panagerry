"""Rilevamento batterie, valutazione soglie, eventi e notifiche."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_STATE_CHANGED
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import (
    CONF_EXCLUDE,
    CONF_NOTIFY_SERVICES,
    CONF_PERSISTENT,
    CONF_RENOTIFY_HOURS,
    CONF_THRESHOLD_MV,
    CONF_THRESHOLD_PCT,
    DEFAULT_RENOTIFY_HOURS,
    DEFAULT_THRESHOLD_MV,
    DEFAULT_THRESHOLD_PCT,
    DOMAIN,
    EVENT_LOW,
    EVENT_RECOVERED,
    SIGNAL_UPDATED,
)

KIND_LEVEL = "level"  # sensor % (device_class battery)
KIND_BINARY = "binary"  # binary_sensor battery (on = scarica)
KIND_VOLTAGE = "voltage"  # sensor tensione della batteria

TEXTS = {
    "it": {
        "title": "Batteria scarica: {name}",
        "level": "carica {value}%",
        "voltage": "tensione {value} mV",
        "binary": "segnalata come scarica",
    },
    "en": {
        "title": "Low battery: {name}",
        "level": "level {value}%",
        "voltage": "voltage {value} mV",
        "binary": "reported low",
    },
}


@dataclass
class Battery:
    """Una batteria (un dispositivo, o una singola entità se senza dispositivo)."""

    key: str
    name: str
    entities: dict[str, str] = field(default_factory=dict)  # entity_id -> kind
    level: float | None = None
    voltage_mv: float | None = None
    binary_low: bool | None = None
    low: bool = False
    reasons: list[str] = field(default_factory=list)

    @property
    def primary(self) -> str:
        for kind in (KIND_LEVEL, KIND_BINARY, KIND_VOLTAGE):
            for eid, k in self.entities.items():
                if k == kind:
                    return eid
        return next(iter(self.entities))

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "entity_id": self.primary,
            "level": self.level,
            "voltage_mv": self.voltage_mv,
            "low": self.low,
            "reasons": self.reasons,
        }


def _num(value: str | None) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class BatteryManager:
    """Gestisce scansione, stato e notifiche."""

    def __init__(self, hass: HomeAssistant, options: dict[str, Any]) -> None:
        self.hass = hass
        self.options = options
        self.batteries: dict[str, Battery] = {}
        self._tracked: dict[str, str] = {}  # entity_id -> key
        self._notified: dict[str, float] = {}  # key -> timestamp ultima notifica
        self._store: Store = Store(hass, 1, f"{DOMAIN}.notified")
        self._unsubs: list[CALLBACK_TYPE] = []
        self._rescan_cancel: CALLBACK_TYPE | None = None

    # ---- opzioni -------------------------------------------------------
    @property
    def pct(self) -> float:
        return float(self.options.get(CONF_THRESHOLD_PCT, DEFAULT_THRESHOLD_PCT))

    @property
    def mv(self) -> float:
        return float(self.options.get(CONF_THRESHOLD_MV, DEFAULT_THRESHOLD_MV))

    @property
    def renotify(self) -> float:
        return float(self.options.get(CONF_RENOTIFY_HOURS, DEFAULT_RENOTIFY_HOURS))

    # ---- ciclo di vita -------------------------------------------------
    async def async_start(self) -> None:
        self._notified = await self._store.async_load() or {}
        if self.hass.is_running:
            self._start()
        else:
            self._unsubs.append(
                self.hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STARTED, lambda _e: self._start()
                )
            )

    @callback
    def _start(self) -> None:
        self.rescan()
        self._unsubs.append(
            self.hass.bus.async_listen(EVENT_STATE_CHANGED, self._state_changed)
        )
        self._unsubs.append(
            self.hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED, self._registry_changed
            )
        )
        self._unsubs.append(
            async_track_time_interval(
                self.hass, self._periodic, timedelta(minutes=10)
            )
        )

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        if self._rescan_cancel:
            self._rescan_cancel()
            self._rescan_cancel = None

    # ---- scansione -----------------------------------------------------
    @callback
    def rescan(self, *_: Any) -> None:
        self._rescan_cancel = None
        ent_reg = er.async_get(self.hass)
        dev_reg = dr.async_get(self.hass)
        exclude = set(self.options.get(CONF_EXCLUDE) or [])
        found: dict[str, Battery] = {}

        for state in self.hass.states.async_all(("sensor", "binary_sensor")):
            eid = state.entity_id
            if eid in exclude:
                continue
            kind = self._classify(state)
            if kind is None:
                continue
            entry = ent_reg.async_get(eid)
            device = (
                dev_reg.async_get(entry.device_id) if entry and entry.device_id else None
            )
            if device:
                key = device.id
                name = device.name_by_user or device.name or state.name
            else:
                key = eid
                name = state.name
            battery = found.setdefault(key, Battery(key=key, name=name))
            battery.entities[eid] = kind

        self.batteries = found
        self._tracked = {
            eid: b.key for b in found.values() for eid in b.entities
        }
        # batterie sparite: pulisce notifiche e stato
        for key in [k for k in self._notified if k not in found]:
            self._notified.pop(key)
            self._dismiss(key)
        self._evaluate_all()

    @staticmethod
    def _classify(state) -> str | None:
        dc = state.attributes.get("device_class")
        domain = state.domain
        if dc == "battery":
            return KIND_LEVEL if domain == "sensor" else KIND_BINARY
        if domain == "sensor" and dc == "voltage":
            eid = state.entity_id.lower()
            if "batter" in eid or "vbat" in eid:
                return KIND_VOLTAGE
        return None

    # ---- valutazione ---------------------------------------------------
    def _read(self, b: Battery) -> bool:
        """Aggiorna i valori. Ritorna False se tutto è non disponibile."""
        b.level = b.voltage_mv = b.binary_low = None
        for eid, kind in b.entities.items():
            state = self.hass.states.get(eid)
            if state is None or state.state in ("unknown", "unavailable"):
                continue
            if kind == KIND_LEVEL:
                b.level = _num(state.state)
            elif kind == KIND_BINARY:
                b.binary_low = state.state == "on"
            else:
                v = _num(state.state)
                if v is not None:
                    unit = state.attributes.get("unit_of_measurement")
                    b.voltage_mv = round(v * 1000, 1) if unit == "V" else v
        return not (b.level is None and b.voltage_mv is None and b.binary_low is None)

    @callback
    def _evaluate(self, b: Battery) -> None:
        if not self._read(b):
            # non disponibile: mantiene l'ultimo stato noto
            b.low = b.key in self._notified
            return
        reasons = []
        if b.level is not None and b.level < self.pct:
            reasons.append("percent")
        if self.mv > 0 and b.voltage_mv is not None and b.voltage_mv < self.mv:
            reasons.append("voltage")
        if b.binary_low:
            reasons.append("binary")
        b.reasons = reasons
        b.low = bool(reasons)
        self._process(b)

    @callback
    def _evaluate_all(self) -> None:
        for b in self.batteries.values():
            self._evaluate(b)
        self._save()
        async_dispatcher_send(self.hass, SIGNAL_UPDATED)

    @callback
    def _process(self, b: Battery) -> None:
        now = time.time()
        last = self._notified.get(b.key)
        if b.low:
            interval = self.renotify * 3600
            if last is None or (interval > 0 and now - last >= interval):
                self._notified[b.key] = now
                self._alert(b, repeat=last is not None)
        elif last is not None:
            self._notified.pop(b.key)
            self._dismiss(b.key)
            self.hass.bus.async_fire(EVENT_RECOVERED, self._event_data(b, False))

    def _event_data(self, b: Battery, repeat: bool) -> dict[str, Any]:
        return {
            **b.as_dict(),
            "device_id": b.key if b.key != b.primary else None,
            "threshold_pct": self.pct,
            "threshold_mv": self.mv,
            "repeat": repeat,
        }

    def _detail(self, b: Battery) -> str:
        t = TEXTS.get(self.hass.config.language[:2], TEXTS["en"])
        parts = []
        if "percent" in b.reasons:
            parts.append(t["level"].format(value=round(b.level)))
        if "voltage" in b.reasons:
            parts.append(t["voltage"].format(value=round(b.voltage_mv)))
        if "binary" in b.reasons:
            parts.append(t["binary"])
        return ", ".join(parts)

    @callback
    def _alert(self, b: Battery, repeat: bool) -> None:
        self.hass.bus.async_fire(EVENT_LOW, self._event_data(b, repeat))
        t = TEXTS.get(self.hass.config.language[:2], TEXTS["en"])
        title = t["title"].format(name=b.name)
        message = f"{b.name}: {self._detail(b)}"
        if self.options.get(CONF_PERSISTENT, True):
            persistent_notification.async_create(
                self.hass, message, title=title, notification_id=self._nid(b.key)
            )
        for service in self.options.get(CONF_NOTIFY_SERVICES) or []:
            domain, _, name = service.partition(".")
            if domain and name:
                self.hass.async_create_task(
                    self.hass.services.async_call(
                        domain,
                        name,
                        {"title": title, "message": message},
                        blocking=False,
                    )
                )

    @staticmethod
    def _nid(key: str) -> str:
        return f"{DOMAIN}_{key.replace('.', '_')}"

    @callback
    def _dismiss(self, key: str) -> None:
        persistent_notification.async_dismiss(self.hass, self._nid(key))

    @callback
    def _save(self) -> None:
        self._store.async_delay_save(lambda: dict(self._notified), 5)

    # ---- listener ------------------------------------------------------
    @callback
    def _state_changed(self, event: Event) -> None:
        eid = event.data["entity_id"]
        key = self._tracked.get(eid)
        if key and key in self.batteries:
            self._evaluate(self.batteries[key])
            self._save()
            async_dispatcher_send(self.hass, SIGNAL_UPDATED)
        elif event.data.get("old_state") is None and eid.split(".")[0] in (
            "sensor",
            "binary_sensor",
        ):
            self._schedule_rescan()  # nuova entità

    @callback
    def _registry_changed(self, event: Event) -> None:
        if event.data.get("entity_id", "").split(".")[0] in ("sensor", "binary_sensor"):
            self._schedule_rescan()

    @callback
    def _schedule_rescan(self) -> None:
        if self._rescan_cancel is None:
            self._rescan_cancel = async_call_later(self.hass, 10, self.rescan)

    @callback
    def _periodic(self, _now: Any) -> None:
        self._evaluate_all()

    # ---- dati per i sensori -------------------------------------------
    def listing(self) -> list[dict[str, Any]]:
        items = sorted(
            self.batteries.values(),
            key=lambda b: (b.level is None, b.level if b.level is not None else 0),
        )
        return [b.as_dict() for b in items]
