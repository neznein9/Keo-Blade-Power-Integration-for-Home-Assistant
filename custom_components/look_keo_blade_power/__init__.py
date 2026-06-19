import logging

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN
from .const import DEBUG_BLUETOOTH
from .pedal import LookPedal
from .services import async_register_services
# from .services import dump_service_info

LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BUTTON,
]


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    if DEBUG_BLUETOOTH:
        _dump_hass_entries(hass)

    await async_register_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    address = entry.data.get("address")
    # address = entry.data.get("address").upper()
    if not address:
        LOGGER.warning("Config entry missing address: %s", entry.entry_id)
        if DEBUG_BLUETOOTH:
            LOGGER.warning("ENTRY ID=%s TITLE=%s DATA=%s", entry.entry_id, entry.title, entry.data)
        return False

    pedal = LookPedal.from_config_entry(entry)
    await pedal.load(hass)
    LOGGER.info("Configured LOOK pedal: %s (%s)", pedal.name, pedal.address)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = pedal

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if DEBUG_BLUETOOTH:
        _dump_entry(entry)

    def _advertisement_callback(service_info: bluetooth.BluetoothServiceInfoBleak, change: bluetooth.BluetoothChange) -> None:
        try:
            # if DEBUG_BLUETOOTH:
            #     dump_service_info(service_info)
            pedal.update_from_advertisement(service_info, hass)
            LOGGER.debug("PEDAL %s advertisements=%s", pedal.name, pedal.advertisement_count)
            async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}_updated")
        except Exception:
            LOGGER.error("Failed to process BT advertisement")

    cancel_callback = bluetooth.async_register_callback(
        hass,
        _advertisement_callback,
        {"address": address.upper()},
        BluetoothScanningMode.ACTIVE,
    )

    entry.async_on_unload(cancel_callback)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN)
        if domain_data is not None:
            domain_data.pop(entry.entry_id, None)
            if not domain_data:
                hass.data.pop(DOMAIN, None)
    return unload_ok


def _dump_hass_entries(hass: HomeAssistant) -> None:
    LOGGER.debug("BEGIN DUMP")
    for config_entry in hass.config_entries.async_entries(DOMAIN):
        LOGGER.debug("ENTRY: %s title=%s data=%s", config_entry.entry_id, config_entry.title, config_entry.data)
    LOGGER.debug("END DUMP")


def _dump_entry(entry: ConfigEntry) -> None:
    LOGGER.debug("ENTRY ID=%s TITLE=%s DATA=%s UNIQUE_ID=%s", entry.entry_id, entry.title, entry.data, entry.unique_id)
