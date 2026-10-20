"""UniFi Protect Alarm Bridge integration."""

from __future__ import annotations

import aiohttp
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.util.ssl import get_default_context

from .api import AuthFailed, MfaRequired, UniFiAlarmClient, UniFiAlarmError
from .const import CONF_CERTIFICATE_FINGERPRINT, CONF_SOURCE_ENTRY_ID
from .coordinator import (
    UniFiAlarmConfigEntry,
    UniFiAlarmCoordinator,
    async_delete_entry_issues,
)
from .shared import SharedProtectClient

PLATFORMS = [Platform.ALARM_CONTROL_PANEL]


async def async_setup_entry(hass: HomeAssistant, entry: UniFiAlarmConfigEntry) -> bool:
    """Set up the console from a config entry."""
    shared = CONF_SOURCE_ENTRY_ID in entry.data
    fingerprint = entry.data.get(CONF_CERTIFICATE_FINGERPRINT)
    if shared:
        client = SharedProtectClient(
            hass, entry.data[CONF_SOURCE_ENTRY_ID], fingerprint
        )
    else:
        session = async_create_clientsession(
            hass, verify_ssl=True, cookie_jar=aiohttp.CookieJar(unsafe=True)
        )
        client = UniFiAlarmClient(
            session,
            entry.data[CONF_HOST],
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
            ssl_context=(
                aiohttp.Fingerprint(bytes.fromhex(fingerprint))
                if fingerprint
                else get_default_context()
            ),
        )
    try:
        console = await client.async_get_console_info()
    except (AuthFailed, MfaRequired) as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except UniFiAlarmError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = UniFiAlarmCoordinator(
        hass, entry, client, console, use_push=not shared
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    coordinator.async_start_push()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: UniFiAlarmConfigEntry) -> bool:
    """Unload a config entry (the socket task and session close automatically)."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: UniFiAlarmConfigEntry) -> None:
    """Delete this entry's repair issues."""
    async_delete_entry_issues(hass, entry.entry_id)
