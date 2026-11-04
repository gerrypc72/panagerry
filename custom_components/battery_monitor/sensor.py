"""Sensori riepilogativi: batterie totali e batterie scariche."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_UPDATED
from .manager import BatteryManager


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: BatteryManager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BatterySummary(manager, entry, "batteries", "Batteries", False),
            BatterySummary(manager, entry, "low_batteries", "Low batteries", True),
        ]
    )


class BatterySummary(SensorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_icon = "mdi:battery-alert-variant-outline"
    _attr_native_unit_of_measurement = "batterie"
    _unrecorded_attributes = frozenset({"batteries"})

    def __init__(self, manager, entry, key, name, only_low) -> None:
        self._manager = manager
        self._only_low = only_low
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = f"Battery Monitor {name}"

    def _items(self) -> list[dict]:
        items = self._manager.listing()
        return [i for i in items if i["low"]] if self._only_low else items

    @property
    def native_value(self) -> int:
        return len(self._items())

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "batteries": self._items(),
            "threshold_pct": self._manager.pct,
            "threshold_mv": self._manager.mv,
        }

    async def async_added_to_hass(self) -> None:
        @callback
        def _update() -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_UPDATED, _update)
        )
