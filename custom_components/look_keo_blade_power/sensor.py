import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)

from .const import (DOMAIN, DEBUG_TAG)
from .pedal import LookPedal


LOGGER = logging.getLogger(__name__)

AD_TYPES = {
    0x01: "Flags",
    0x03: "Complete 16-bit UUIDs",
    0x07: "Complete 128-bit UUIDs",
    0x09: "Complete Local Name",
    0x19: "Appearance",
    0xFF: "Manufacturer Specific Data",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    pedal: LookPedal = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            LookPedalAdvertisementCountSensor(pedal),
            LookPedalRSSISensor(pedal),
            LookPedalLastSeenSensor(pedal),

            LookPedalEntryIdSensor(pedal), # DEBUG
            LookPedalAddressSensor(pedal),
            LookPedalLocalNameSensor(pedal),
            LookPedalConnectableSensor(pedal),
            LookPedalTxPowerSensor(pedal),
            LookPedalRawAdvertisementSensor(pedal),

            LookPedalBatteryPercentSensor(pedal),
            LookPedalLastBatteryReadSensor(pedal),
            LookPedalLastBTRequestSensor(pedal),

            LookPedalManufacturerSensor(pedal),
            LookPedalModelNoSensor(pedal),
            LookPedalSerialNoSensor(pedal),
            LookPedalHardwareRevSensor(pedal),
            LookPedalFirmwareRevSensor(pedal),
            LookPedalSoftwareRevSensor(pedal),
            LookPedalSystemIdSensor(pedal),
            LookPedalPnPSensor(pedal),
        ]
    )


# Base Class
class LookPedalSensor(SensorEntity):
    sensor_key = None
    sensor_name = None

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, pedal: LookPedal):
        self.pedal = pedal
        self._attr_name = self.sensor_name
        self._attr_unique_id = (f"{pedal.address}_{self.sensor_key}_{DEBUG_TAG}")

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self.pedal.entry_id}_updated",
                self._handle_update,
            )
        )

    @property
    def device_info(
        self,
    ) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.pedal.address)},
            manufacturer="LOOK",
            model="Keo Blade Power",
            name=self.pedal.name,
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class LookPedalAdvertisementCountSensor(LookPedalSensor):
    sensor_key = f"advertisement_count"
    sensor_name = "Advertisement Count"
    _attr_icon = "mdi:radio-tower"

    @property
    def native_value(self):
        return self.pedal.advertisement_count


class LookPedalRSSISensor(LookPedalSensor):
    sensor_key = f"rssi"
    sensor_name = "RSSI"
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def icon(self):
        rssi = self.pedal.rssi
        if rssi is None:
            return "mdi:signal-cellular-outline"
        if rssi >= -50:
            return "mdi:signal-cellular-3"
        if rssi >= -65:
            return "mdi:signal-cellular-2"
        if rssi >= -80:
            return "mdi:signal-cellular-1"
        return "mdi:signal-cellular-outline"

    @property
    def native_value(self):
        return self.pedal.rssi


class LookPedalLastSeenSensor(LookPedalSensor):
    sensor_key = f"last_seen"
    sensor_name = "Last Seen"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"
    @property
    def native_value(self):
        return self.pedal.last_seen


class LookPedalRawAdvertisementSensor(
    LookPedalSensor,
):
    sensor_key = f"ble_packet"
    sensor_name = "BLE Packet"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:code-json"
    _attr_entity_registry_visible_default = False
    @property
    def native_value(self):
        if self.pedal.raw is None:
            return None
        return f"{len(self.pedal.raw)} bytes"

    @property
    def extra_state_attributes(self):
        return {
            "raw_hex": (
                self.pedal.raw.hex()
                if self.pedal.raw
                else None
            ),

            "name": self.pedal.local_name,
            "address": self.pedal.address,
            "rssi": self.pedal.rssi,
            "manufacturer_data": str(self.pedal.manufacturer_data),
            "service_uuids": self.pedal.service_uuids,
            "connectable": self.pedal.connectable,
            "time": self.pedal.time,
            "tx_power": self.pedal.tx_power,
            "parsed_hex": self.parse_advertisement(self.pedal.raw)
        }

    @staticmethod
    def parse_advertisement(raw: bytes) -> list[dict]:
        results = []

        if not raw:
            return results

        index = 0
        while index < len(raw):
            length = raw[index]

            if length == 0:
                break

            ad_type = raw[index + 1]
            data_start = index + 2
            data_end = index + 1 + length

            data = raw[data_start:data_end]

            results.append({
                "type": ad_type,
                "name": AD_TYPES.get(
                    ad_type,
                    f"Unknown (0x{ad_type:02X})",
                ),
                "data_hex": data.hex(),
            })



            index += length + 1
        return results


class LookPedalAddressSensor(LookPedalSensor):
    sensor_key = f"mac_address"
    sensor_name = "MAC"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = True
    # _attr_entity_registry_visible_default = False
    _attr_icon = "mdi:bluetooth"
    @property
    def native_value(self):
        return self.pedal.address



class LookPedalEntryIdSensor(LookPedalSensor):
    sensor_key = f"entry_id"
    sensor_name = "HA Entry ID"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = True
    _attr_entity_registry_visible_default = False
    _attr_icon = "mdi:information"
    @property
    def native_value(self):
        return self.pedal.entry_id[:10] + "..."


class LookPedalLocalNameSensor(LookPedalSensor):
    sensor_key = f"local_name"
    sensor_name = "Local Name"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = True
    # _attr_entity_registry_visible_default = False
    _attr_icon = "mdi:tag-text-outline"
    @property
    def native_value(self):
        return self.pedal.local_name


class LookPedalTxPowerSensor(LookPedalSensor):
    sensor_key = f"tx_power"
    sensor_name = "Tx Power"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = True
    _attr_icon = "mdi:antenna"
    @property
    def native_value(self):
        return self.pedal.tx_power


class LookPedalConnectableSensor(LookPedalSensor):
    sensor_key = f"connectable"
    sensor_name = "Connectable"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_visible_default = False
    _attr_icon = "mdi:bluetooth-connect"
    @property
    def native_value(self):
        return self.pedal.connectable


class LookPedalBatteryPercentSensor(LookPedalSensor):
    sensor_key = f"battery_percent"
    sensor_name = "Battery"

    _attr_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_entity_registry_visible_default = True

    @property
    def icon(self):
        pct = self.pedal.battery_percent
        if pct is None:
            return "mdi:battery-unknown"
        if pct > 99:
            return "mdi:battery"
        if pct >= 90:
            return "mdi:battery-90"
        if pct >= 80:
            return "mdi:battery-80"
        if pct >= 70:
            return "mdi:battery-70"
        if pct >= 60:
            return "mdi:battery-60"
        if pct >= 50:
            return "mdi:battery-50"
        if pct >= 40:
            return "mdi:battery-40"
        if pct >= 30:
            return "mdi:battery-30"
        if pct >= 20:
            return "mdi:battery-20"
        if pct >= 10:
            return "mdi:battery-10"
        return "mdi:battery-outline"

    @property
    def native_value(self):
        return self.pedal.battery_percent



class LookPedalLastBatteryReadSensor(LookPedalSensor):
    sensor_key = f"battery_last_read"
    sensor_name = "Last Battery Read"

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:code-json"

    @property
    def native_value(self):
        return self.pedal.last_battery_read


class LookPedalLastBTRequestSensor(LookPedalSensor):
    sensor_key = f"bt_last_request"
    sensor_name = "Last BT Request"

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:code-json"

    @property
    def native_value(self):
        return self.pedal.bt_last_request_result

    @property
    def extra_state_attributes(self):
        return {
            "command": self.pedal.bt_last_request_command,
            "attribute": self.pedal.bt_last_request_gatt_short,
            "uuid": self.pedal.bt_last_request_gatt_long,
            "log": self.pedal.bt_last_request_log,
            "last_attempt": self.pedal.bt_last_request_timestamp,
            "connection_established": self.pedal.bt_last_request_connected,
            "bytes": self.pedal.bt_last_request_bytes,
            "disconnected": self.pedal.bt_last_request_disconnected,
            "delta seconds": self.pedal.bt_last_request_delta_seconds,
        }


class LookPedalManufacturerSensor(LookPedalSensor):
    sensor_key = f"manufacturer"
    sensor_name = "Manufacturer"
    _attr_icon = "mdi:factory"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.pedal.manufacturer_name


class LookPedalModelNoSensor(LookPedalSensor):
    sensor_key = f"model_no"
    sensor_name = "Model"
    _attr_icon = "mdi:sail-boat"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.pedal.model_number


class LookPedalSerialNoSensor(LookPedalSensor):
    sensor_key = f"serial_no"
    sensor_name = "Serial"
    _attr_icon = "mdi:barcode"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.pedal.serial_number


class LookPedalHardwareRevSensor(LookPedalSensor):
    sensor_key = f"hardware_rev"
    sensor_name = "Hardware Revision"
    _attr_icon = "mdi:progress-wrench"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.pedal.hardware_revision


class LookPedalFirmwareRevSensor(LookPedalSensor):
    sensor_key = f"firmware_rev"
    sensor_name = "Firmware Revision"
    _attr_icon = "mdi:progress-star-four-points"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.pedal.firmware_revision


class LookPedalSoftwareRevSensor(LookPedalSensor):
    sensor_key = f"software_rev"
    sensor_name = "Software Revision"
    _attr_icon = "mdi:progress-pencil"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.pedal.software_revision


class LookPedalSystemIdSensor(LookPedalSensor):
    sensor_key = f"system_id"
    sensor_name = "System ID"
    _attr_icon = "mdi:identifier"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.pedal.system_id

    @property
    def extra_state_attributes(self):
        return {
            "company identifier": None, #40 Least Significant bits (right side bits)
            "organization id (OUI)": None, #24 Most Significant bits (left side bits)
        }


class LookPedalPnPSensor(LookPedalSensor):
    sensor_key = f"pnp_id"
    sensor_name = "Plug-and-Play Id"
    _attr_icon = "mdi:connection"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    @property
    def native_value(self):
        return self.pedal.pnp_id

    @property
    def extra_state_attributes(self):
        return {
            "vendor id": None,
            "product id": None,
            "product version": None,
        }
