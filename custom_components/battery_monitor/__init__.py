"""Battery Monitor: elenca le batterie, notifica sotto soglia, genera eventi."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, SERVICE_RESCAN
from .manager import BatteryManager

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def _rescan(_call: ServiceCall) -> None:
        for manager in hass.data.get(DOMAIN, {}).values():
            manager.rescan()

    hass.services.async_register(DOMAIN, SERVICE_RESCAN, _rescan)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    manager = BatteryManager(hass, dict(entry.options))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager
    await manager.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id).async_stop()
    return ok
