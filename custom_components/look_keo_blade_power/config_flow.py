import voluptuous as vol

from homeassistant import config_entries
from .const import DOMAIN


class LookKeoBladePowerConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:

            for entry in self._async_current_entries():
                if entry.data.get("address") == user_input["address"]:
                    return self.async_abort(
                        reason="already_configured"
                    )

            return self.async_create_entry(
                title=user_input["address"],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("address"): str,
                }
            ),
        )
