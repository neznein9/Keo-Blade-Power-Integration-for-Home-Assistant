import logging
import time

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from bleak import BleakClient
from bleak_retry_connector import establish_connection

from . import bt_helper
from .const import DOMAIN


LOGGER = logging.getLogger(__name__)

async def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "read_battery"):
        return


    # async def delete_all_entries(call):
    #     entries = list(hass.config_entries.async_entries(DOMAIN))

    #     LOGGER.warning("Deleting %s LOOK Keo Blade Power config entries", len(entries))

    #     for config_entry in entries:
    #         LOGGER.warning(
    #             "Deleting LOOK entry: id=%s title=%s data=%s",
    #             config_entry.entry_id,
    #             config_entry.title,
    #             config_entry.data,
    #         )
    #         await hass.config_entries.async_remove(config_entry.entry_id)


    # async def dump_devices(call):
    #     registry = dr.async_get(hass)
    #     for device in registry.devices.values():
    #         LOGGER.warning("DEVICE id=%s name=%s identifiers=%s", device.id, device.name, device.identifiers)


    # async def probe_bluetooth_connection_info(call):
    #     address = call.data.get("address")

    #     if not address:
    #         LOGGER.warning("Missing address")
    #         return

    #     service_info = bluetooth.async_last_service_info(hass, address, connectable=True)
    #     ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    #     scanner_devices = bluetooth.async_scanner_devices_by_address(hass, address, connectable=True)
    #     present = bluetooth.async_address_present(hass, address, connectable=True)

    #     LOGGER.warning(
    #         "BT PROBE\naddress: %s\npresent: %s\nservice_info: %s\nble_device: %s\nscanner_devices: %s\ntype(ble_device): %s",
    #         address, present, service_info, ble_device, scanner_devices, type(ble_device),
    #     )


    # async def probe_gatt_services(call):
    #     address = call.data.get("address")

    #     if not address:
    #         LOGGER.warning("Missing address")
    #         return

    #     ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    #     if ble_device is None:
    #         LOGGER.warning("Device not available: %s", address)
    #         return

    #     LOGGER.warning("Connecting to %s", address)

    #     client = None
    #     try:
    #         client = await establish_connection(BleakClient, ble_device, ble_device.address)
    #         for service in client.services:
    #             LOGGER.warning("SERVICE %s", bt_helper.describe_uuid(service.uuid))
    #             for characteristic in service.characteristics:
    #                 LOGGER.warning("CHARACTERISTIC %s properties=%s", characteristic.uuid, characteristic.properties)
    #     except Exception:
    #         LOGGER.exception("Failed GATT probe")
    #     finally:
    #         if client and client.is_connected:
    #             await client.disconnect()


    async def read_battery(call):
        address = call.data.get("address")

        if not address:
            LOGGER.warning("Missing address")
            return

        ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
        if ble_device is None:
            LOGGER.warning("Device not available: %s", address)
            return

        start = time.monotonic()
        client = None

        try:
            client = await establish_connection(BleakClient, ble_device, ble_device.address)
            LOGGER.info("Connected to %s", address)
            battery_bytes = await client.read_gatt_char("00002a19-0000-1000-8000-00805f9b34fb")
            if not battery_bytes:
                LOGGER.warning("Battery characteristic returned empty payload")
                return
            battery_percent = int(battery_bytes[0])
            LOGGER.debug("BATTERY RAW=%s PERCENT=%s", battery_bytes, battery_percent)
        except Exception:
            LOGGER.error("Battery read failed")
        finally:
            if client and client.is_connected:
                await client.disconnect()
            LOGGER.info("Disconnected from %s", address)

        LOGGER.info("Battery read completed in %.2f sec", time.monotonic() - start)

    hass.services.async_register(DOMAIN, "read_battery", read_battery)
    # hass.services.async_register(DOMAIN, "delete_all_entries", delete_all_entries)
    # hass.services.async_register(DOMAIN, "dump_devices", dump_devices)
    # hass.services.async_register(DOMAIN, "probe_bluetooth_connection_info", probe_bluetooth_connection_info)
    # hass.services.async_register(DOMAIN, "probe_gatt_services", probe_gatt_services)


# def dump_service_info(service_info) -> None:
#     if service_info is None:
#         LOGGER.warning("LOOK BLE: service_info=None")
#         return
#     LOGGER.warning(
#         "LOOK BLE: name=%s address=%s rssi=%s manufacturer=%s services=%s",
#         service_info.name, service_info.address, service_info.rssi, service_info.manufacturer_data, service_info.service_uuids
#     )
