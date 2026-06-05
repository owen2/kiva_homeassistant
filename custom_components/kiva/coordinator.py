"""DataUpdateCoordinator for Kiva."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from oauthlib.oauth1 import Client as OAuth1Client

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    KIVA_MY_ACCOUNT_URL,
    UPDATE_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class KivaCoordinator(DataUpdateCoordinator):
    """Fetches Kiva account data on a schedule."""

    def __init__(
        self,
        hass: HomeAssistant,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_token_secret: str,
    ) -> None:
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    def _build_auth_header(self) -> str:
        """Return an OAuth 1.0 Authorization header for the account endpoint."""
        client = OAuth1Client(
            client_key=self._consumer_key,
            client_secret=self._consumer_secret,
            resource_owner_key=self._access_token,
            resource_owner_secret=self._access_token_secret,
        )
        _, headers, _ = client.sign(KIVA_MY_ACCOUNT_URL, http_method="GET")
        return headers["Authorization"]

    async def _async_update_data(self) -> dict:
        auth_header = await self.hass.async_add_executor_job(self._build_auth_header)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    KIVA_MY_ACCOUNT_URL,
                    headers={"Authorization": auth_header},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        raise UpdateFailed("Invalid Kiva credentials (401 Unauthorized)")
                    if resp.status != 200:
                        raise UpdateFailed(f"Kiva API returned HTTP {resp.status}")
                    payload = await resp.json()
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Cannot connect to Kiva API: {err}") from err

        account = payload.get("my_account")
        if not account:
            raise UpdateFailed("Unexpected Kiva API response: missing 'my_account'")
        return account
