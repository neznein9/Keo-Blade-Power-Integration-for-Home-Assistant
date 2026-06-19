# from homeassistant.config_entries import ConfigEntry
# from homeassistant.core import HomeAssistant
# from homeassistant.helpers.device_registry import DeviceInfo
# from homeassistant.helpers.entity import EntityCategory
# from homeassistant.components.binary_sensor import BinarySensorEntity

# from .const import DOMAIN
# from .pedal import LookPedal


# async def async_setup_entry(
#     hass: HomeAssistant,
#     entry: ConfigEntry,
#     async_add_entities,
# ) -> None:
#     pedal: LookPedal = hass.data[DOMAIN][entry.entry_id]
#     async_add_entities(
#         [
#             # LookPedalConnectableBinarySensor(pedal),
#         ]
#     )


# # Base Class
# class LookPedalBinarySensor(BinarySensorEntity):
#     binary_sensor_key = None
#     binary_sensor_name = None

#     _should_poll = False
#     _attr_has_entity_name = True

#     def __init__(self, pedal: LookPedal):
#         self.pedal = pedal
#         self._attr_name = self.binary_sensor_name
#         self._attr_unique_id = f"{pedal.address}_{self.binary_sensor_key}"

#     @property
#     def device_info(self) -> DeviceInfo:
#         return DeviceInfo(
#             identifiers={(DOMAIN, self.pedal.address)},
#             manufacturer="LOOK",
#             model="Keo Blade Power",
#             name=self.pedal.name,
#         )


# # class LookPedalConnectableBinarySensor(LookPedalBinarySensor):
# #     binary_sensor_key = "connectable"
# #     binary_sensor_name = "Connectable"

# #     _attr_entity_category = EntityCategory.DIAGNOSTIC
# #     _attr_entity_registry_enabled_default = True
# #     _attr_icon = "mdi:bluetooth-connect"

# #     @property
# #     def is_on(self) -> bool | None:
# #         return self.pedal.connectable
