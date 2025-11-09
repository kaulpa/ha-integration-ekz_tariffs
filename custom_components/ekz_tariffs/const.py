"""Constants for the EKZ Energy Tariffs integration."""
DOMAIN = "ekz_tariffs"
API_ENDPOINT = "https://api.tariffs.ekz.ch/v1/tariffs"

CONF_UPDATE_TIME = "update_time"
DEFAULT_UPDATE_TIME = "18:00"

# Basic attributes
ATTR_NEXT_UPDATE = "next_update"
ATTR_LOWEST_PRICE = "lowest_price"
ATTR_LOWEST_PRICE_TIME = "lowest_price_time"
ATTR_LOWEST_PRICE_DURATION = "lowest_price_duration"  # Duration in minutes

# Period attributes
ATTR_CURRENT_PERIOD_START = "current_period_start"
ATTR_CURRENT_PERIOD_END = "current_period_end"

# Price component attributes
ATTR_ELECTRICITY_PRICE = "electricity_CHF_per_kWh"
ATTR_ELECTRICITY_BASE = "electricity_CHF_per_M"
ATTR_GRID_PRICE = "grid_CHF_per_kWh"
ATTR_GRID_BASE = "grid_CHF_per_M"
ATTR_INTEGRATED_PRICE = "integrated_CHF_per_kWh"
ATTR_INTEGRATED_BASE = "integrated_CHF_per_M"
ATTR_REGIONAL_FEES_PRICE = "regional_fees_CHF_per_kWh"
ATTR_REGIONAL_FEES_BASE = "regional_fees_CHF_per_M"

COORDINATOR = "coordinator"