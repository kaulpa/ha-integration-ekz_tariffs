"""Sensor platform for EKZ Energy Tariffs integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any
from zoneinfo import ZoneInfo

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    ATTR_LOWEST_PRICE,
    ATTR_LOWEST_PRICE_TIME,
    ATTR_LOWEST_PRICE_DURATION,
    ATTR_NEXT_UPDATE,
    COORDINATOR,
    DOMAIN,
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EKZ Energy Tariffs sensor."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    async_add_entities([EKZTariffSensor(coordinator)])

class EKZTariffSensor(CoordinatorEntity, SensorEntity):
    """Representation of an EKZ Energy Tariff sensor."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "CHF/kWh"
    _attr_has_entity_name = True
    _attr_name = "EKZ Energy Tariff"
    _attr_unique_id = "ekz_energy_tariff"

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "ekz_tariffs")},
            "name": "EKZ Energy Tariffs",
            "manufacturer": "EKZ",
            "model": "Tariff API",
        }

    @property
    def native_value(self) -> float | None:
        """Return the current energy price."""
        if not self.coordinator.data:
            return None
        
        try:
            # Get current time in UTC
            now = datetime.now().astimezone()
            
            # Find the matching period
            for period in self.coordinator.data:
                # Parse timestamps with timezone information
                start = datetime.fromisoformat(period["startDate"])
                end = datetime.fromisoformat(period["endDate"])
                
                if start <= now < end:
                    return float(period["price"])
            
            # If we didn't find a matching period, log a warning
            _LOGGER.warning(
                "No price data found for current time %s. First available period: %s to %s",
                now.isoformat(),
                self.coordinator.data[0]["startDate"] if self.coordinator.data else "N/A",
                self.coordinator.data[0]["endDate"] if self.coordinator.data else "N/A"
            )
            return None
            
        except (KeyError, ValueError, TypeError) as error:
            _LOGGER.error("Error processing price data: %s", error)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}
        
        if not self.coordinator.data:
            return attributes

        try:
            # Get current time with timezone information
            now = datetime.now().astimezone()
            current_period = None
            
            # Find current period and calculate lowest price info
            lowest_price = float('inf')
            lowest_price_time = None
            lowest_price_duration = 0
            current_duration = 0
            last_price = None
            last_start = None

            for period in sorted(self.coordinator.data, key=lambda x: x["startDate"]):
                start = datetime.fromisoformat(period["startDate"])
                end = datetime.fromisoformat(period["endDate"])
                
                # Find current period
                if start <= now < end:
                    current_period = period
                
                # Calculate lowest price periods
                price = float(period["price"])
                if price < lowest_price:
                    lowest_price = price
                    lowest_price_time = start
                    lowest_price_duration = 1
                    current_duration = 1
                elif price == last_price:
                    current_duration += 1
                    if current_duration > lowest_price_duration:
                        lowest_price = price
                        lowest_price_time = last_start
                        lowest_price_duration = current_duration
                else:
                    current_duration = 1
                
                last_price = price
                last_start = start

            # Add lowest price information
            attributes[ATTR_LOWEST_PRICE] = lowest_price
            attributes[ATTR_LOWEST_PRICE_TIME] = lowest_price_time.isoformat() if lowest_price_time else None
            attributes[ATTR_LOWEST_PRICE_DURATION] = lowest_price_duration * 15  # Convert to minutes

            # Calculate next update time
            update_time = datetime.strptime(self.coordinator.config_entry.data.get("update_time", "18:00"), "%H:%M").time()
            next_update = datetime.combine(now.date(), update_time)
            if now.time() >= update_time:
                next_update += timedelta(days=1)
            attributes[ATTR_NEXT_UPDATE] = next_update.astimezone().isoformat()

            # Add current period details if available
            if current_period:
                # Add all price components from current period
                for key, value in current_period.items():
                    if key not in ["startDate", "endDate", "price"]:  # Skip these as they're handled separately
                        attributes[key] = value
                
                # Add formatted start and end times
                attributes["current_period_start"] = current_period["startDate"]
                attributes["current_period_end"] = current_period["endDate"]

        except Exception as error:
            _LOGGER.error("Error calculating attributes: %s", error)

        return attributes