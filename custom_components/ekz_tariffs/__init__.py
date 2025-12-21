"""The EKZ Energy Tariffs integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_ENDPOINT,
    CONF_UPDATE_TIME,
    COORDINATOR,
    DEFAULT_UPDATE_TIME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EKZ Energy Tariffs from a config entry."""
    update_time = entry.data.get(CONF_UPDATE_TIME, DEFAULT_UPDATE_TIME)
    
    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(10):
                session = async_get_clientsession(hass)
                async with session.get(API_ENDPOINT) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Error communicating with API: {resp.status}")
                    data = await resp.json()
                    
                    _LOGGER.debug("Received data from API: %s", data)
                    
                    # Get the prices list from the response
                    if not isinstance(data, dict) or "prices" not in data:
                        raise UpdateFailed("Invalid API response format")
                    
                    prices = data["prices"]
                    if not prices:
                        raise UpdateFailed("No price data received from API")
                    
                    # Process and format the price data
                    formatted_data = []
                    for period in prices:
                        try:
                            # Extract all price components
                            price_data = {
                                "startDate": period["start_timestamp"],
                                "endDate": period["end_timestamp"]
                            }
                            
                            # Process each price component
                            for component in ["electricity", "grid", "integrated", "regional_fees"]:
                                if component in period:
                                    for price in period[component]:
                                        key = f"{component}_{price['unit'].replace('/', '_per_')}"
                                        price_data[key] = float(price["value"])
                            
                            # Get main price (integrated CHF/kWh) for sorting and primary value
                            integrated_kwh = next(
                                (p["value"] for p in period["integrated"] if p["unit"] in ["CHF/kWh", "CHF_kWh"]),
                                None
                            )
                            
                            if integrated_kwh is not None:
                                price_data["price"] = float(integrated_kwh)
                                formatted_data.append(price_data)
                        except (KeyError, ValueError, TypeError) as e:
                            _LOGGER.warning("Error processing period %s: %s", period, e)
                            continue
                    
                    if not formatted_data:
                        raise UpdateFailed("No valid price data found in API response")
                    
                    # Sort data by startDate
                    sorted_data = sorted(formatted_data, key=lambda x: x["startDate"])
                    _LOGGER.debug("Processed %d price periods", len(sorted_data))
                    return sorted_data

        except asyncio.TimeoutError as error:
            _LOGGER.error("Timeout communicating with EKZ API")
            raise UpdateFailed("Timeout communicating with API") from error
        except (aiohttp.ClientError, ValueError) as error:
            _LOGGER.error("Error communicating with EKZ API: %s", error)
            raise UpdateFailed(f"Error communicating with API: {error}") from error
        except Exception as error:
            _LOGGER.error("Unexpected error processing API data: %s", error)
            raise UpdateFailed(f"Error processing API data: {error}") from error

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        # Update once per day at specified time
        update_interval=timedelta(days=1),
    )

    # Schedule the first update
    now = datetime.now()
    update_time_obj = datetime.strptime(update_time, "%H:%M").time()
    next_update = datetime.combine(now.date(), update_time_obj)
    if now.time() >= update_time_obj:
        next_update += timedelta(days=1)
    
    async def schedule_update():
        await coordinator.async_refresh()
        hass.async_create_task(schedule_next_update())

    update_task = None
    
    async def schedule_next_update():
        """Schedule the next update."""
        try:
            while True:
                next_time = datetime.combine(datetime.now().date(), update_time_obj)
                if datetime.now().time() >= update_time_obj:
                    next_time += timedelta(days=1)
                delay = (next_time - datetime.now()).total_seconds()
                
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    _LOGGER.debug("Update task cancelled")
                    raise
                
                await coordinator.async_refresh()
        except asyncio.CancelledError:
            _LOGGER.debug("Update loop cancelled")
            raise

    # Store coordinator and update task for platforms to access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    # Start the update task
    update_task = asyncio.create_task(schedule_next_update())
    hass.data[DOMAIN][entry.entry_id]["update_task"] = update_task

    # Register service to manually refresh data
    async def handle_refresh_service(call):
        """Handle the manual refresh service call."""
        _LOGGER.info("Manual refresh of EKZ tariff data requested")
        await coordinator.async_refresh()

    hass.services.async_register(
        DOMAIN,
        "refresh_data",
        handle_refresh_service
    )

    # Get initial data
    await coordinator.async_config_entry_first_refresh()
    hass.async_create_task(schedule_next_update())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        # Cancel the update task if it exists
        if "update_task" in hass.data[DOMAIN][entry.entry_id]:
            update_task = hass.data[DOMAIN][entry.entry_id]["update_task"]
            if not update_task.done():
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass
        
        # Remove the entry data
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unload_ok