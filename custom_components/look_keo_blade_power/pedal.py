import logging
import time
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.dt import now, parse_datetime
from homeassistant.helpers.storage import Store
from bleak import BleakClient
from bleak_retry_connector import establish_connection
from bleak_retry_connector import BleakNotFoundError
from bleak_retry_connector import BleakOutOfConnectionSlotsError

from . import bt_helper
from .const import DOMAIN


LOGGER = logging.getLogger(__name__)


class LookPedal:
    def __init__(self, address: str, name: str):
        # from HA
        self.address = address.upper()
        self.entry_id = None
        self.name = name

        self.last_save = None
        self.save_in_progress = False
        self.last_battery_poll_request = None
        self.last_device_poll_request = None
        self.battery_poll_in_flight = False
        self.device_poll_in_flight = False

        # from passive BLE advertisement
        self.local_name = None
        self.advertisement_count = 0
        self.last_seen = None
        self.last_service_info = None
        self.time = None
        self.rssi = None
        self.tx_power = None
        self.manufacturer_data = {}
        self.service_uuids = []
        self.connectable = False
        self.raw = None

        # from active BLE connection polling
        self.battery_percent = None
        self.last_battery_read = None

        self.manufacturer_name = None
        self.model_number = None
        self.serial_number = None
        self.hardware_revision = None
        self.firmware_revision = None
        self.software_revision = None
        self.system_id = None
        self.pnp_id = None

        # Trackers shared across all BT calls
        self.bt_last_request_command = None
        self.bt_last_request_gatt_short = None
        self.bt_last_request_gatt_long = None
        self.bt_last_request_result = None
        self.bt_last_request_log = None
        self.bt_last_request_timestamp = None
        self.bt_last_request_connected = None
        self.bt_last_request_bytes = None
        self.bt_last_request_disconnected = None
        self.bt_last_request_delta_seconds = None

    @classmethod
    def from_config_entry(cls, entry: ConfigEntry) -> "LookPedal":
        pedal = cls(
            address=entry.data["address"].upper(),
            name=entry.title,
        )
        pedal.entry_id = entry.entry_id
        return pedal

    def update_from_advertisement(self, service_info: bluetooth.BluetoothServiceInfoBleak, hass: HomeAssistant) -> None:
        self.advertisement_count += 1
        self.last_service_info = service_info
        self.last_seen = now()
        self.time = service_info.time
        self.rssi = service_info.rssi
        self.tx_power = service_info.tx_power
        self.raw = service_info.raw

        if service_info.name:
            self.name = service_info.name

        if (
            service_info.advertisement is not None
            and service_info.advertisement.local_name
        ):
            self.local_name = service_info.advertisement.local_name

        if service_info.manufacturer_data:
            self.manufacturer_data = service_info.manufacturer_data

        if service_info.service_uuids:
            self.service_uuids = service_info.service_uuids

        if service_info.connectable is not None:
            self.connectable = service_info.connectable

        if not self.last_device_poll_request or time.monotonic() - self.last_device_poll_request > 86400:
            if not self.device_poll_in_flight:
                asyncio.create_task(self.read_device_data(hass))
            return

        if not self.last_battery_poll_request or time.monotonic() - self.last_battery_poll_request > 3600:
            if not self.battery_poll_in_flight:
                asyncio.create_task(self.read_battery(hass))
            return

        if not self.last_save or time.monotonic() - self.last_save > 5:
            asyncio.create_task(self._save_background(hass))

    def _begin_request(self, command: str, uuid: str | None = None) -> None:
        self.bt_last_request_command = command
        self.bt_last_request_gatt_short = bt_helper.describe_uuid(uuid) if uuid else None
        self.bt_last_request_gatt_long = uuid
        self.bt_last_request_result = None
        self.bt_last_request_log = None
        self.bt_last_request_timestamp = now()
        self.bt_last_request_connected = None
        self.bt_last_request_bytes = None
        self.bt_last_request_disconnected = None
        self.bt_last_request_delta_seconds = None

    def _ble_precondition(self, hass: HomeAssistant) -> tuple[bool, BLEDevice | None]:
        """Check BLE availability. Returns (True, ble_device) or (False, None) after setting result state."""
        if not bluetooth.async_address_present(hass, self.address, connectable=True):
            LOGGER.info("Device is not currently awake: %s", self.address)
            self.bt_last_request_result = "Sleeping"
            self.bt_last_request_log = "Pedal is offline or sleeping"
            return False, None

        if self.last_seen is None:
            self.bt_last_request_result = "Missing"
            self.bt_last_request_log = "Pedal has never been seen"
            return False, None

        seconds_since_seen = (now() - self.last_seen).total_seconds()
        if seconds_since_seen > 120:
            LOGGER.info("Skipping read; pedal not recently seen")
            self.bt_last_request_result = "Sleeping"
            self.bt_last_request_log = f"Pedal has not advertised for {seconds_since_seen:.1f} seconds (120 max)"
            return False, None

        ble_device = bluetooth.async_ble_device_from_address(hass, self.address, connectable=True)
        if ble_device is None:
            LOGGER.info("Device not available: %s", self.address)
            self.bt_last_request_result = "Unavailable"
            self.bt_last_request_log = "Pedal is not available"
            return False, None

        return True, ble_device

    async def read_battery(self, hass: HomeAssistant) -> int | None:
        if self.battery_poll_in_flight:
            return
        self.battery_poll_in_flight = True

        uuid = bt_helper.BATTERY_LEVEL_UUID
        self._begin_request("read_battery", uuid)

        ok, ble_device = self._ble_precondition(hass)
        if not ok:
            self.battery_poll_in_flight = False
            return None

        client = None
        start = time.monotonic()
        try:
            client = await establish_connection(BleakClient, ble_device, ble_device.address)
            LOGGER.info("Connected to %s", ble_device.address)
            self.bt_last_request_connected = now()

            LOGGER.info("read_battery CONNECTED=%s BEFORE READ %s", client.is_connected, bt_helper.describe_uuid(uuid))
            battery_bytes = await asyncio.wait_for(client.read_gatt_char(uuid), timeout=5)

            if not battery_bytes:
                LOGGER.error("Battery read returned empty payload")
                self.bt_last_request_result = "Empty response"
                self.bt_last_request_log = "Empty payload returned"
                return None

            self.bt_last_request_bytes = battery_bytes.hex()
            battery_percent = int(battery_bytes[0])

            if battery_percent > 100:
                LOGGER.warning("Unexpected battery percentage: %s", battery_percent)

            self.battery_percent = battery_percent
            self.last_battery_read = now()
            LOGGER.debug("BATTERY RAW=%s PERCENT=%s", battery_bytes, battery_percent)
            self.bt_last_request_result = "Success"
            self.bt_last_request_log = f"Battery read success: RAW={battery_bytes}, PCT={battery_percent}"
            self.last_battery_poll_request = time.monotonic()
            return battery_percent
        except BleakNotFoundError:
            LOGGER.info("Pedal unavailable or asleep: %s", self.address)
            self.bt_last_request_result = "Not found"
            self.bt_last_request_log = "BleakNotFoundError: Pedal is offline or asleep"
            return None
        except BleakOutOfConnectionSlotsError:
            LOGGER.info("No BLE connection slot available for %s", self.address)
            self.bt_last_request_result = "Connection denied"
            self.bt_last_request_log = "BleakOutOfConnectionSlotsError: Pedal refused connection"
            return None
        except Exception:
            LOGGER.error("Unexpected battery read failure")
            self.bt_last_request_result = "Error"
            self.bt_last_request_log = "Exception: Unexpected failure"
            return None
        finally:
            if client and client.is_connected:
                await client.disconnect()
            elapsed = time.monotonic() - start
            self.bt_last_request_disconnected = now()
            self.bt_last_request_delta_seconds = elapsed
            LOGGER.debug("Battery read completed in %.2f sec", elapsed)
            self.battery_poll_in_flight = False
            await self.save(hass)

    def clear_device_data(self, hass: HomeAssistant) -> None:
        self.manufacturer_name = None
        self.model_number = None
        self.serial_number = None
        self.hardware_revision = None
        self.firmware_revision = None
        self.software_revision = None
        self.system_id = None
        self.pnp_id = None
        self.last_device_poll_request = None
        asyncio.create_task(self._save_background(hass))

    async def read_device_data(self, hass: HomeAssistant) -> None:
        if self.device_poll_in_flight:
            return
        self.device_poll_in_flight = True

        self._begin_request("read_device_data")

        ok, ble_device = self._ble_precondition(hass)
        if not ok:
            self.device_poll_in_flight = False
            return

        client = None
        start = time.monotonic()
        try:
            client = await establish_connection(BleakClient, ble_device, ble_device.address)
            LOGGER.info("Connected to %s", self.address)
            self.bt_last_request_connected = now()

            await self.read_utf8_characteristic_if_empty(client, "manufacturer_name", bt_helper.MANUFACTURER_NAME_UUID)
            await self.read_utf8_characteristic_if_empty(client, "model_number", bt_helper.MODEL_NUMBER_UUID)
            await self.read_utf8_characteristic_if_empty(client, "serial_number", bt_helper.SERIAL_NUMBER_UUID)
            await self.read_utf8_characteristic_if_empty(client, "hardware_revision", bt_helper.HARDWARE_REVISION_UUID)
            await self.read_utf8_characteristic_if_empty(client, "firmware_revision", bt_helper.FIRMWARE_REVISION_UUID)
            await self.read_utf8_characteristic_if_empty(client, "software_revision", bt_helper.SOFTWARE_REVISION_UUID)
            await self.read_system_id_if_empty(client)
            await self.read_pnp_id_if_empty(client)

            self.bt_last_request_result = "Success"
            self.bt_last_request_log = "All fields successfully polled"
            self.last_device_poll_request = time.monotonic()
        except BleakNotFoundError:
            LOGGER.info("Pedal unavailable or asleep: %s", self.address)
            self.bt_last_request_result = "Not found"
            self.bt_last_request_log = "BleakNotFoundError: Pedal is offline or asleep"
        except BleakOutOfConnectionSlotsError:
            LOGGER.info("No BLE connection slot available for %s", self.address)
            self.bt_last_request_result = "Connection denied"
            self.bt_last_request_log = "BleakOutOfConnectionSlotsError: Pedal refused connection"
        except Exception:
            LOGGER.error("Unexpected read failure")
            self.bt_last_request_result = "Error"
            self.bt_last_request_log = "Exception: Unexpected failure"
        finally:
            if client and client.is_connected:
                await client.disconnect()
            elapsed = time.monotonic() - start
            self.bt_last_request_disconnected = now()
            self.bt_last_request_delta_seconds = elapsed
            LOGGER.debug("Device read completed in %.2f sec", elapsed)
            self.device_poll_in_flight = False
            await self.save(hass)
            if not self.last_battery_poll_request or time.monotonic() - self.last_battery_poll_request > 3600:
                asyncio.create_task(self.read_battery(hass))

    async def read_utf8_characteristic_if_empty(self, client, field_name: str, uuid: str) -> str | None:
        if getattr(self, field_name) is not None:
            return getattr(self, field_name)

        uuid_desc = bt_helper.describe_uuid(uuid)
        self.bt_last_request_gatt_short = uuid_desc
        self.bt_last_request_gatt_long = uuid

        LOGGER.debug("read_utf8_characteristic CONNECTED=%s BEFORE READ %s", client.is_connected, uuid_desc)
        raw = await asyncio.wait_for(client.read_gatt_char(uuid), timeout=5)

        if not raw:
            self.bt_last_request_bytes = None
            self.bt_last_request_result = "Empty response"
            self.bt_last_request_log = f"{uuid_desc} returned empty payload"
            return None

        self.bt_last_request_bytes = raw.hex()
        self.bt_last_request_result = "..."
        self.bt_last_request_log = f"{uuid_desc} read success"

        value = raw.decode("utf-8", errors="replace").strip("\x00").strip()
        setattr(self, field_name, value)
        return value

    async def read_system_id_if_empty(self, client) -> str | None:
        if self.system_id is not None:
            return self.system_id

        uuid = bt_helper.SYSTEM_ID_UUID
        uuid_desc = bt_helper.describe_uuid(uuid)
        self.bt_last_request_gatt_short = uuid_desc
        self.bt_last_request_gatt_long = uuid

        LOGGER.debug("read_system_id CONNECTED=%s BEFORE READ %s", client.is_connected, uuid_desc)
        raw = await asyncio.wait_for(client.read_gatt_char(uuid), timeout=5)

        if not raw:
            self.bt_last_request_bytes = None
            self.bt_last_request_result = "Empty response"
            self.bt_last_request_log = f"{uuid_desc} returned empty payload"
            return None

        LOGGER.debug("SYSTEM ID RAW=%s LEN=%s", raw.hex().upper(), len(raw))
        self.bt_last_request_bytes = raw.hex()
        self.bt_last_request_result = "..."
        self.bt_last_request_log = f"{uuid_desc} read success"

        self.system_id = raw.hex().upper()
        return self.system_id

    async def read_pnp_id_if_empty(self, client) -> dict | None:
        if self.pnp_id is not None:
            return self.pnp_id

        uuid = bt_helper.PNP_ID_UUID
        uuid_desc = bt_helper.describe_uuid(uuid)
        self.bt_last_request_gatt_short = uuid_desc
        self.bt_last_request_gatt_long = uuid

        LOGGER.debug("read_pnp_if_empty CONNECTED=%s BEFORE READ %s", client.is_connected, uuid_desc)
        raw = await asyncio.wait_for(client.read_gatt_char(uuid), timeout=5)

        if not raw:
            self.bt_last_request_bytes = None
            self.bt_last_request_result = "Empty response"
            self.bt_last_request_log = f"{uuid_desc} returned empty payload"
            return None

        LOGGER.debug("PNP ID RAW=%s LEN=%s", raw.hex(), len(raw))
        self.bt_last_request_bytes = raw.hex()
        self.pnp_id = {
            "raw": raw.hex(),
            "vendor_id_source": raw[0],
            "vendor_id": int.from_bytes(raw[1:3], "little"),
            "product_id": int.from_bytes(raw[3:5], "little"),
            "product_version": int.from_bytes(raw[5:7], "little"),
        }
        LOGGER.debug("PNP: %s", self.pnp_id)
        self.bt_last_request_result = "..."
        self.bt_last_request_log = f"{uuid_desc} read success"
        return self.pnp_id

    def _store(self, hass: HomeAssistant) -> Store:
        return Store(hass, 1, f"look_keo_blade_power/{DOMAIN}_{self.address}")

    async def _save_background(self, hass: HomeAssistant) -> None:
        try:
            await self.save(hass)
        except Exception:
            LOGGER.error("Failed to save pedal state")

    async def save(self, hass: HomeAssistant) -> None:
        if self.save_in_progress:
            return
        self.save_in_progress = True
        LOGGER.debug("Saving device: %s", self.address)
        try:
            store = self._store(hass)
            await store.async_save({
                "advertisement_count": self.advertisement_count,
                "last_seen": self.last_seen.isoformat() if self.last_seen else None,
                "local_name": self.local_name,
                "battery_percent": self.battery_percent,
                "last_battery_read": self.last_battery_read.isoformat() if self.last_battery_read else None,
                "manufacturer_name": self.manufacturer_name,
                "model_number": self.model_number,
                "serial_number": self.serial_number,
                "hardware_revision": self.hardware_revision,
                "firmware_revision": self.firmware_revision,
                "software_revision": self.software_revision,
                "system_id": self.system_id,
                "pnp_id": self.pnp_id,
            })
            self.last_save = time.monotonic()
            LOGGER.debug("Save successful: %s", self.address)
        finally:
            self.save_in_progress = False

    async def load(self, hass: HomeAssistant) -> None:
        store = self._store(hass)
        data = await store.async_load()
        if not data:
            return
        if "advertisement_count" in data:
            self.advertisement_count = data["advertisement_count"]
        if "last_seen" in data and data["last_seen"]:
            self.last_seen = parse_datetime(data["last_seen"])
        if "local_name" in data and data["local_name"]:
            self.local_name = data["local_name"]
        if "battery_percent" in data:
            self.battery_percent = data["battery_percent"]
        if "last_battery_read" in data and data["last_battery_read"]:
            self.last_battery_read = parse_datetime(data["last_battery_read"])
        if "manufacturer_name" in data and data["manufacturer_name"]:
            self.manufacturer_name = data["manufacturer_name"]
        if "model_number" in data and data["model_number"]:
            self.model_number = data["model_number"]
        if "serial_number" in data and data["serial_number"]:
            self.serial_number = data["serial_number"]
        if "hardware_revision" in data and data["hardware_revision"]:
            self.hardware_revision = data["hardware_revision"]
        if "firmware_revision" in data and data["firmware_revision"]:
            self.firmware_revision = data["firmware_revision"]
        if "software_revision" in data and data["software_revision"]:
            self.software_revision = data["software_revision"]
        if "system_id" in data and data["system_id"]:
            self.system_id = data["system_id"]
        if "pnp_id" in data and data["pnp_id"]:
            self.pnp_id = data["pnp_id"]
        LOGGER.debug("Loaded device: %s", self.address)
