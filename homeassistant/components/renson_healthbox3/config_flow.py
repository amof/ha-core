"""Config flow for Renson integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from pyhealthbox3.healthbox3 import (
    Healthbox3,
    Healthbox3ApiClientAuthenticationError,
    Healthbox3ApiClientCommunicationError,
    Healthbox3ApiClientError,
)
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.URL,
                autocomplete="url",
            ),
        ),
        vol.Optional(CONF_API_KEY): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
            ),
        ),
    }
)


class RensonConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Renson Healthbox."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        if user_input is not None and not (
            errors := await self.validate_input(user_input)
        ):
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Renson Healthbox3", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        reconf_entry = self._get_reconfigure_entry()

        if user_input:
            if not (errors := await self.validate_input(user_input)):
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    reconf_entry, data_updates=user_input
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=STEP_USER_DATA_SCHEMA,
                suggested_values={
                    CONF_HOST: reconf_entry.data[CONF_HOST],
                    CONF_API_KEY: reconf_entry.data.get(CONF_API_KEY, None),
                },
            ),
            errors=errors,
        )

    async def validate_input(self, user_input: Mapping[str, Any]) -> dict[str, str]:
        """Auth Helper."""

        errors: dict[str, str] = {}
        session = async_create_clientsession(self.hass)
        client = Healthbox3(
            host=user_input[CONF_HOST],
            api_key=user_input.get(CONF_API_KEY, None),
            session=session,
        )
        try:
            if CONF_API_KEY in user_input:
                await client.async_enable_advanced_api_features()
            await client.async_validate_connectivity()
        except Healthbox3ApiClientAuthenticationError:
            errors["base"] = "auth"
        except Healthbox3ApiClientCommunicationError:
            errors["base"] = "connection"
        except Healthbox3ApiClientError:
            errors["base"] = "unknown"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(client.host)
        return errors
