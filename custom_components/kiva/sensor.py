"""Kiva balance sensor."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KivaCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: KivaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([KivaBalanceSensor(coordinator, entry)])


class KivaBalanceSensor(CoordinatorEntity[KivaCoordinator], SensorEntity):
    """Sensor representing a Kiva account balance."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY_DOLLAR
    _attr_icon = "mdi:hand-coin"

    def __init__(self, coordinator: KivaCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        lender_id = (coordinator.data or {}).get("lender_id", entry.entry_id)
        self._attr_unique_id = f"{lender_id}_balance"
        self._attr_name = f"{entry.title} Balance"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Kiva",
            configuration_url="https://www.kiva.org/portfolio",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("balance")

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        return {
            k: data[k]
            for k in ("lender_id", "name", "currency_code")
            if k in data
        }
