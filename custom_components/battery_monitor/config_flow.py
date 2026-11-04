"""Configurazione e opzioni."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

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
)


def _num(max_: int, unit: str) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0, max=max_, step=1, mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )


def _schema(hass, cur: dict[str, Any]) -> vol.Schema:
    services = sorted(
        f"notify.{name}" for name in hass.services.async_services().get("notify", {})
        if name not in ("send_message", "persistent_notification")
    )
    return vol.Schema(
        {
            vol.Required(
                CONF_THRESHOLD_PCT, default=cur.get(CONF_THRESHOLD_PCT, DEFAULT_THRESHOLD_PCT)
            ): _num(100, "%"),
            vol.Required(
                CONF_THRESHOLD_MV, default=cur.get(CONF_THRESHOLD_MV, DEFAULT_THRESHOLD_MV)
            ): _num(10000, "mV"),
            vol.Required(
                CONF_RENOTIFY_HOURS, default=cur.get(CONF_RENOTIFY_HOURS, DEFAULT_RENOTIFY_HOURS)
            ): _num(720, "h"),
            vol.Required(
                CONF_PERSISTENT, default=cur.get(CONF_PERSISTENT, True)
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_NOTIFY_SERVICES, default=cur.get(CONF_NOTIFY_SERVICES, [])
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=services, multiple=True, custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_EXCLUDE, default=cur.get(CONF_EXCLUDE, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["sensor", "binary_sensor"], multiple=True
                )
            ),
        }
    )


def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
    out = dict(user_input)
    for k in (CONF_THRESHOLD_PCT, CONF_THRESHOLD_MV, CONF_RENOTIFY_HOURS):
        out[k] = int(out[k])
    return out


class BatteryMonitorFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(
                title="Battery Monitor", data={}, options=_clean(user_input)
            )
        return self.async_show_form(step_id="user", data_schema=_schema(self.hass, {}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BatteryMonitorOptions()


class BatteryMonitorOptions(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(data=_clean(user_input))
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(self.hass, dict(self.config_entry.options)),
        )
