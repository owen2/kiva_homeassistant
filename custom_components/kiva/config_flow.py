"""Config flow for Kiva integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from oauthlib.oauth1 import Client as OAuth1Client
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_ACCESS_TOKEN_SECRET,
    CONF_CONSUMER_KEY,
    CONF_CONSUMER_SECRET,
    DOMAIN,
    KIVA_MY_ACCOUNT_URL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONSUMER_KEY): str,
        vol.Required(CONF_CONSUMER_SECRET): str,
        vol.Required(CONF_ACCESS_TOKEN): str,
        vol.Required(CONF_ACCESS_TOKEN_SECRET): str,
    }
)


def _sign_request(
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_token_secret: str,
) -> str:
    client = OAuth1Client(
        client_key=consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )
    _, headers, _ = client.sign(KIVA_MY_ACCOUNT_URL, http_method="GET")
    return headers["Authorization"]


async def _validate_credentials(
    hass,
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    access_token_secret: str,
) -> dict:
    """Validate credentials by hitting the Kiva API. Returns account data on success."""
    auth_header = await hass.async_add_executor_job(
        _sign_request, consumer_key, consumer_secret, access_token, access_token_secret
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                KIVA_MY_ACCOUNT_URL,
                headers={"Authorization": auth_header},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 401:
                    raise InvalidCredentials
                if resp.status != 200:
                    raise CannotConnect(f"HTTP {resp.status}")
                payload = await resp.json()
    except aiohttp.ClientError as err:
        raise CannotConnect from err

    account = payload.get("my_account")
    if not account:
        raise CannotConnect("Unexpected API response")
    return account


class KivaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kiva."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                account = await _validate_credentials(
                    self.hass,
                    user_input[CONF_CONSUMER_KEY],
                    user_input[CONF_CONSUMER_SECRET],
                    user_input[CONF_ACCESS_TOKEN],
                    user_input[CONF_ACCESS_TOKEN_SECRET],
                )
            except InvalidCredentials:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Kiva credential validation")
                errors["base"] = "unknown"
            else:
                lender_id = account.get("lender_id", "kiva")
                await self.async_set_unique_id(lender_id)
                self._abort_if_unique_id_configured()

                title = account.get("name") or f"Kiva ({lender_id})"
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "docs_url": "https://www.kiva.org/build/docs",
            },
        )


class CannotConnect(HomeAssistantError):
    pass


class InvalidCredentials(HomeAssistantError):
    pass
