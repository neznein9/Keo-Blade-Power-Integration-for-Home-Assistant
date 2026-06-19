import re
import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN


MAC_PATTERN = re.compile(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$")

def normalize_address(address: str) -> str:
    return address.strip().upper().replace("-", ":")

def validate_address(address: str) -> str:
    address = normalize_address(address)
    if not MAC_PATTERN.match(address):
        raise vol.Invalid("Invalid BLE MAC address")
    return address


class LookKeoBladePowerConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                address = validate_address(user_input["address"])
            except vol.Invalid:
                errors["address"] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=address, data={"address": address})
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("address"): str}),
            errors=errors,
        )
