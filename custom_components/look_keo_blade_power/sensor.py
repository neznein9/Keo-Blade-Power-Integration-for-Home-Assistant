from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .pedal import LookPedal


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    pedal: LookPedal = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([LookPedalAdvertisementCountSensor(pedal)])


class LookPedalAdvertisementCountSensor(
    SensorEntity,
):
    def __init__(self, pedal: LookPedal):
        self.pedal = pedal

        self._attr_name = "BLE Advertisement Count"
        self._attr_unique_id = (
            f"{pedal.address}_advertisement_count"
        )

    @property
    def native_value(self):
        return self.pedal.advertisement_count

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.pedal.address,
                )
            },
            manufacturer="LOOK",
            model="Keo Blade Power",
            name=self.pedal.name,
        )
