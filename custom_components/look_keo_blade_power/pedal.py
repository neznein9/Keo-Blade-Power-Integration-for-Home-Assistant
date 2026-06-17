import logging
import time
import asyncio

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.dt import now
from homeassistant.helpers.dispatcher import async_dispatcher_send
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
        self.address = address
        self.entry_id = None
        self.name = name

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
        self.bt_last_request_result = None #sensor msg
        self.bt_last_request_log = None
        self.bt_last_request_timestamp = None
        self.bt_last_request_connected = None
        self.bt_last_request_bytes = None
        self.bt_last_request_disconnected = None
        self.bt_last_request_delta_seconds = None


    @classmethod
    def from_config_entry(cls, entry: ConfigEntry) -> "LookPedal":
        pedal = cls(
            address=entry.data["address"],
            name=entry.title,
        )
        pedal.entry_id = entry.entry_id
        return pedal


    def update_from_advertisement(self, service_info: bluetooth.BluetoothServiceInfoBleak) -> None:
        self.advertisement_count += 1
        self.last_service_info = service_info
        self.last_seen = now()
        self.time = service_info.time # this one was visible n .as_dict()
        self.rssi = service_info.rssi
        self.tx_power = service_info.tx_power
        self.raw = service_info.raw;

        if service_info.name:
            self.name = service_info.name

        if (
            service_info.advertisement is not None
            and service_info.advertisement.local_name
        ):
            self.local_name = service_info.advertisement.local_name

        if service_info.manufacturer_data:
            self.manufacturer_data = service_info.manufacturer_data # Should we parse this down? ex {28676: b''}

        if service_info.service_uuids:
            self.service_uuids = service_info.service_uuids #ok that this is an (empty) array?

        if service_info.connectable is not None: # this comes from .as_dict()
            self.connectable = service_info.connectable


    async def read_battery(self, hass: HomeAssistant) -> int | None:
        address = self.address
        uuid = bt_helper.BATTERY_LEVEL_UUID
        self.bt_last_request_command = "read_battery"
        self.bt_last_request_gatt_short = bt_helper.describe_uuid(uuid)
        self.bt_last_request_gatt_long = uuid
        self.bt_last_request_result = None
        self.bt_last_request_log = None
        self.bt_last_request_timestamp = now()
        self.bt_last_request_connected = None
        self.bt_last_request_bytes = None
        self.bt_last_request_disconnected = None
        self.bt_last_request_delta_seconds = None

        if not bluetooth.async_address_present(hass, address, connectable=True):
            LOGGER.warning("Device is not currently awake: %s", address)
            self.bt_last_request_result = "Sleeping"
            self.bt_last_request_log = "Pedal is offline or sleeping"
            return None

        if (self.last_seen is None or (now() - self.last_seen).total_seconds() > 120):
            LOGGER.info("Skipping battery read; pedal not recently seen")
            self.bt_last_request_result = "Sleeping"
            self.bt_last_request_log = f"Pedal has not advertised for {self.last_seen is None or (now() - self.last_seen).total_seconds()} seconds (120 max)"
            return None

        ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
        if ble_device is None:
            LOGGER.warning("Device not available: %s", address)
            self.bt_last_request_result = "Unavailable"
            self.bt_last_request_log = "Pedal is not available"
            return None

        client = None
        start = time.monotonic()
        start_ts = now()
        self.bt_last_request_timestamp = start_ts
        try:
            client = await establish_connection(BleakClient, ble_device, ble_device.address)
            LOGGER.warning("Connected to %s", address)
            LOGGER.info("Connected to %s", address)
            self.bt_last_request_connected = now()

            battery_bytes = await asyncio.wait_for(client.read_gatt_char(uuid), timeout=5)

            if not battery_bytes:
                LOGGER.error("Battery read returned empty payload")
                self.bt_last_request_result = "Empty response"
                self.bt_last_request_log = "Empty payload returned"
                return None

            self.bt_last_request_bytes = battery_bytes.hex()
            battery_percent = int(battery_bytes[0])

            if battery_percent < 0 or battery_percent > 100:
                LOGGER.warning( "Unexpected battery percentage: %s", battery_percent)

            self.battery_percent = battery_percent
            self.last_battery_read = now()
            LOGGER.warning("BATTERY RAW=%s PERCENT=%s", battery_bytes, battery_percent)
            self.bt_last_request_result = "Success"
            self.bt_last_request_log = f"Battery read succcess: RAW={battery_bytes}, PCT={battery_percent}"
            return battery_percent
        except BleakNotFoundError:
            LOGGER.info("Pedal unavailable or asleep: %s", address)
            self.bt_last_request_result = "Not found"
            self.bt_last_request_log = "BleakNotFoundError: Pedal is offline or asleep"
            return None
        except BleakOutOfConnectionSlotsError:
            LOGGER.info("No BLE connection slot available for %s", address)
            self.bt_last_request_result = "Connection denied"
            self.bt_last_request_log = "BleakOutOfConnectionSlotsError: Pedal refused connection"
            return None
        except Exception:
            LOGGER.exception("Unexpected battery read failure")
            self.bt_last_request_result = "Error"
            self.bt_last_request_log = "Exception: Unexpected failure"
            return None
        finally:
            if client and client.is_connected:
                await client.disconnect()
            LOGGER.info("Disconnected from %s", address)
            elapsed = time.monotonic() - start
            self.bt_last_request_disconnected = now()
            self.bt_last_request_delta_seconds = elapsed
            LOGGER.warning("Battery read completed in %.2f sec", elapsed)
