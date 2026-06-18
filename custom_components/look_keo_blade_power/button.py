import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, DEBUG_TAG
from .pedal import LookPedal


LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    pedal: LookPedal = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        LookPedalReadBatteryButton(hass, pedal),
        LookPedalClearDeviceDataButton(hass, pedal),
        LookPedalReadDeviceDataButton(hass, pedal),
    ])

    LOGGER.warning("BUTTON PLATFORM LOADED FOR %s", pedal.address)


class LookPedalButton(ButtonEntity):
    button_key = None
    button_name = None

    def __init__(self, hass: HomeAssistant, pedal: LookPedal):
        self.hass = hass
        self.pedal = pedal
        self._attr_name = self.button_name
        self._attr_unique_id = f"{pedal.address}_{self.button_key}_{DEBUG_TAG}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.pedal.address)},
            manufacturer="LOOK",
            model="Keo Blade Power",
            name=self.pedal.name,
        )


class LookPedalReadBatteryButton(LookPedalButton):
    button_key = "check_battery"
    button_name = "Check Battery"
    _attr_icon = "mdi:battery-sync"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self):
        self.pedal.last_battery_poll_request = None  # Button ignores debounce
        await self.pedal.read_battery(self.hass)
        async_dispatcher_send(self.hass, f"{DOMAIN}_{self.pedal.entry_id}_updated")


class LookPedalClearDeviceDataButton(LookPedalButton):
    button_key = "clear_device_data"
    button_name = "Clear Device Data"
    _attr_icon = "mdi:close-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_visible_default = False

    async def async_press(self):
        self.pedal.clear_device_data(self.hass)
        async_dispatcher_send(self.hass, f"{DOMAIN}_{self.pedal.entry_id}_updated")


class LookPedalReadDeviceDataButton(LookPedalButton):
    button_key = "read_device_data"
    button_name = "Read Device Data"
    _attr_icon = "mdi:leak"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_visible_default = False

    async def async_press(self):
        self.pedal.last_device_poll_request = None  # Button ignores debounce
        await self.pedal.read_device_data(self.hass)
        async_dispatcher_send(self.hass, f"{DOMAIN}_{self.pedal.entry_id}_updated")
