"""Costanti di Battery Monitor."""

DOMAIN = "battery_monitor"

CONF_THRESHOLD_PCT = "threshold_pct"
CONF_THRESHOLD_MV = "threshold_mv"
CONF_RENOTIFY_HOURS = "renotify_hours"
CONF_NOTIFY_SERVICES = "notify_services"
CONF_PERSISTENT = "persistent_notification"
CONF_EXCLUDE = "exclude"

DEFAULT_THRESHOLD_PCT = 20
DEFAULT_THRESHOLD_MV = 0  # 0 = controllo in mV disattivato
DEFAULT_RENOTIFY_HOURS = 24  # 0 = non ripetere

EVENT_LOW = f"{DOMAIN}_low"
EVENT_RECOVERED = f"{DOMAIN}_recovered"

SIGNAL_UPDATED = f"{DOMAIN}_updated"
SERVICE_RESCAN = "rescan"
