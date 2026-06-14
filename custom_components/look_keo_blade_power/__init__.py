import logging

from .const import DOMAIN
from .const import DEBUG_BLUETOOTH
from .pedal import LookPedal
from .services import async_register_services
from .services import dump_service_info
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothScanningMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

PLATFORMS = ["sensor"]
LOGGER = logging.getLogger(__name__)


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:

    # DEBUG BEGIN
    LOGGER.warning("LOOK KEO: starting up...")
    if DEBUG_BLUETOOTH:
        _dump_hass_entries(hass)
    # DEBUG END

    await async_register_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    address = entry.data.get("address")
    if not address:
        LOGGER.warning("Config entry missing address: %s", entry.entry_id)
        LOGGER.warning("ENTRY ID=%s TITLE=%s DATA=%s", entry.entry_id, entry.title, entry.data, )
        return False

    pedal = LookPedal.from_config_entry(entry)
    LOGGER.warning("Configured LOOK pedal: %s (%s)", pedal.name, pedal.address)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = pedal

    # Add entry to Platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # This is defined as a child scope of async_setup_entry
    def _advertisement_callback(service_info: bluetooth.BluetoothServiceInfoBleak, change: bluetooth.BluetoothChange) -> None:
        if DEBUG_BLUETOOTH:
            dump_service_info(service_info)

        pedal.update_from_advertisement(service_info)
        LOGGER.warning("PEDAL %s advertisements=%s", pedal.name, pedal.advertisement_count)

    if DEBUG_BLUETOOTH:
        _dump_entry(entry)

    cancel_callback = bluetooth.async_register_callback(
        hass,
        _advertisement_callback,
        { "address": address },
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
        hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return unload_ok


def _dump_hass_entries(hass: HomeAssistant) -> None:
    LOGGER.warning("BEGIN DUMP")
    for config_entry in hass.config_entries.async_entries(DOMAIN):
        LOGGER.warning(
            "ENTRY: %s title=%s data=%s",
            config_entry.entry_id,
            config_entry.title,
            config_entry.data,
        )
    LOGGER.warning("END DUMP")

def _dump_entry(entry: ConfigEntry) -> None:
    LOGGER.warning(
        "ENTRY ID=%s TITLE=%s DATA=%s UNIQUE_ID=%s",
        entry.entry_id,
        entry.title,
        entry.data,
        entry.unique_id,
    )
