import logging

from .const import DOMAIN

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
