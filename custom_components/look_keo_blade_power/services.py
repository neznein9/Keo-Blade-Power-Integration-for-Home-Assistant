import logging
import time

from .const import DOMAIN
from homeassistant.helpers import device_registry as dr
from homeassistant.components import bluetooth
from bleak import BleakClient
from bleak_retry_connector import establish_connection


LOGGER = logging.getLogger(__name__)


async def async_register_services(hass):
    # return True
    # async def dump_last_bt_advertisement(call):
    #     service_info = hass.data[DOMAIN].get("last_service_info")

    #     if service_info is None:
    #         LOGGER.warning("No advertisement has been received yet.")
    #         return

    #     dump_service_info(service_info)


    # async def dump_device_info(call):
    #     service_info = hass.data[DOMAIN].get("last_service_info")

    #     if service_info is None:
    #         LOGGER.warning("No advertisement has been received yet.")
    #         return

    #     dump_service_info(service_info)

    async def delete_all_entries(call):
        entries = list(hass.config_entries.async_entries(DOMAIN))

        LOGGER.warning(
            "Deleting %s LOOK Keo Blade Power config entries",
            len(entries),
        )

        for config_entry in entries:
            LOGGER.warning(
                "Deleting LOOK entry: id=%s title=%s data=%s",
                config_entry.entry_id,
                config_entry.title,
                config_entry.data,
            )

            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )

    async def dump_devices(call):
        registry = dr.async_get(hass)
        for device in registry.devices.values():
            LOGGER.warning(
                "DEVICE id=%s name=%s identifiers=%s",
                device.id,
                device.name,
                device.identifiers,
            )

    async def probe_bluetooth_connection_info(call):
        address = call.data.get("address")

        if not address:
            LOGGER.warning("Missing address")
            return

        service_info = bluetooth.async_last_service_info(hass, address, connectable=True)
        ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
        scanner_devices = bluetooth.async_scanner_devices_by_address(hass, address, connectable=True)
        present = bluetooth.async_address_present(hass, address, connectable=True)

        s = "BT PROBE"
        s = s + f"address: {address}\n"
        s = s + f"present: {present}\n"
        s = s + f"service_info: {service_info}\n"
        s = s + f"ble_device: {ble_device}\n"
        s = s + f"scanner_devices: {scanner_devices}\n"
        s = s + f"type(ble_device): {type(ble_device)}"
        LOGGER.warning(s)

    async def probe_gatt_services(call):
        address = call.data.get("address")
        ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
        if ble_device is None:
            LOGGER.warning("Device not available: %s", address)
            return

        LOGGER.warning("Connecting to %s", address)

        try:
            async with BleakClient(ble_device) as client:
                services = client.services

                for service in services:
                    LOGGER.warning("SERVICE %s", service.uuid)

                    for characteristic in service.characteristics:
                        LOGGER.warning("CHARACTERISTIC %s properties=%s", characteristic.uuid, characteristic.properties)

        except Exception:
            LOGGER.exception("Failed GATT probe")


    async def read_battery(call):
        address = call.data.get("address")
        ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
        if ble_device is None:
            LOGGER.warning("Device not available: %s", address)
            return

        # LOGGER.warning("Connecting to %s", address)
        start = time.monotonic()
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        LOGGER.warning("Connected to %s", address)

        try:
            battery_bytes = await client.read_gatt_char("00002a19-0000-1000-8000-00805f9b34fb")
            battery_percent = int(battery_bytes[0])
            LOGGER.warning("BATTERY RAW=%s PERCENT=%s", battery_bytes, battery_percent)
        finally:
            await client.disconnect()
            LOGGER.warning("Disconnected from %s", address)

        elapsed = time.monotonic() - start
        LOGGER.warning("Battery read completed in %.2f sec", elapsed)

    # hass.services.async_register(
    #     DOMAIN,
    #     "dump_last_bt_advertisement",
    #     dump_last_bt_advertisement,
    # )

    # hass.services.async_register(
    #     DOMAIN,
    #     "dump_device_info",
    #     dump_device_info,
    # )

    hass.services.async_register(
        DOMAIN,
        "delete_all_entries",
        delete_all_entries,
    )

    hass.services.async_register(
        DOMAIN,
        "dump_devices",
        dump_devices,
    )

    hass.services.async_register(
        DOMAIN,
        "probe_bluetooth_connection_info",
        probe_bluetooth_connection_info,
    )

    hass.services.async_register(
        DOMAIN,
        "probe_gatt_services",
        probe_gatt_services,
    )

    hass.services.async_register(
        DOMAIN,
        "read_battery",
        read_battery
    )


def dump_service_info(service_info):
    LOGGER.warning(
        "LOOK BLE: name=%s address=%s rssi=%s manufacturer=%s services=%s",
        service_info.name,
        service_info.address,
        service_info.rssi,
        service_info.manufacturer_data,
        service_info.service_uuids,
    )

    # LOGGER.warning("INFO: %s", service_info)
    # LOGGER.warning("TYPE: %s", type(service_info))
    # LOGGER.warning("DIR: %s", dir(service_info))
    # LOGGER.warning("DEVICE: %s", service_info.device)
    # LOGGER.warning("RAW: %s", service_info.raw)
    # LOGGER.warning("ATTR_DICT: %s", getattr(service_info, "__dict__", None))
    # LOGGER.warning("DICT KEYS: %s", service_info.__class__.__dict__.keys())
    # LOGGER.warning("DICT: %s", service_info.as_dict())
    # LOGGER.warning("MRO: %s", service_info.__class__.__mro__)
    # LOGGER.warning("ADV: %s", service_info.advertisement)
    # LOGGER.warning("ADV DIR: %s", dir(service_info.advertisement))
    # LOGGER.warning("ADV: %r", service_info.advertisement)
