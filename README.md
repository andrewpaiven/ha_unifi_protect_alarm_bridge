# About this fork

This is an independently maintained MIT-licensed fork of
[violuke/ha_unifi_protect_alarm_bridge](https://github.com/violuke/ha_unifi_protect_alarm_bridge), based on v1.0.1.
The original author is not responsible for these changes.

- When an official UniFi Protect integration exists, setup reuses its current
  authenticated session. No password is copied, and the account's permissions
  are not expanded. This mode polls every 15 seconds and has no separate websocket.
- Dedicated-account setup remains available when no existing Protect entry exists.
  HTTPS requires a trusted certificate or an exact SHA-256 certificate pin.
- The panel supports mapped Away, Home and Night modes and explicit Disarm.
  **Disarm first before changing modes.** There is no automatic disarm-then-arm
  sequence and no automatic re-arming after a failed request.
- Every control decision starts with a fresh, verified Global-mode profile read.
  Unknown state blocks arming. A disarm request reaches every discovered profile
  even when the last read said it was disarmed. Failed requests are surfaced;
  transport errors never trigger a blind retry of a write.
- Late action replies cannot replace an intervening update. Older timestamped
  pushes are ignored. Polling runs independently of pushes, and authentication
  failures immediately make the entity unavailable.

This remains an unofficial integration using undocumented UniFi APIs. Software
tests use a fake console; they do not certify a security system or a real alarm
control transition. Keep a backup before installation. The existing official
Protect integration must remain enabled when session reuse is selected.

# UniFi Protect Alarm Bridge

A Home Assistant alarm panel for UniFi Protect's **Global Alarm Manager**.

Protect switches Alarm Manager to Global mode as soon as sensors, relays, fobs or
an Alarm Hub are adopted. In Global mode the public Protect API cannot arm,
disarm or read the arm state, so the official UniFi Protect integration cannot
offer an alarm panel. This integration talks to Alarm Manager directly:

- **State** comes from Alarm Manager's arm profiles. Session reuse polls every
  15 seconds. Dedicated-account mode also receives websocket updates, with
  polling every 60 seconds while connected and every 10 seconds otherwise.
- **Arm and disarm** call Alarm Manager's own profile actions.
- The panel shows `disarmed`, `arming` (during the exit delay), `armed_away`,
  `armed_home` or `armed_night`, and `triggered`. It never assumes a state it
  hasn't read from the console.

Session reuse depends on the official UniFi Protect integration remaining loaded.
Dedicated-account mode can run independently.

> **Unofficial.** This uses undocumented UniFi OS APIs, which a firmware update
> could change. If that happens you'll get a repair notice in Home Assistant
> rather than a silently wrong alarm state.

## Prerequisites

1. **Protect's Alarm Manager in Global mode, with at least one arm profile.**
2. **An existing authenticated Protect integration with sufficient alarm permissions**,
   or a dedicated local Super Admin account. For dedicated-account mode, create one under
   **Admins & Users → Add Admin**:
   - **Restrict to local access only.** No UI.com cloud account.
   - **No two-factor authentication.** Home Assistant cannot answer an MFA
     challenge.
   - **Role: Super Admin.** Alarm Manager is a UniFi OS feature, and no custom
     role grants it. Testing showed that Protect "Full Management", Network
     "Site Admin" and user-management "View Only" are all refused.

> **Security note.** Home Assistant stores these credentials unencrypted in
> `.storage/core.config_entries`, and a Super Admin can control the whole
> console, including network, cameras and users. That's why the account should
> be dedicated to Home Assistant, local-only, and used for nothing else. Remove
> it if you stop using this integration.

## Installation (HACS)

1. In HACS, open **⋮ → Custom repositories**. Add
   `https://github.com/andrewpaiven/ha_unifi_protect_alarm_bridge` with the category
   **Integration**.
2. Download it, then restart Home Assistant.

## Setup

1. Go to **Settings → Devices & services → Add integration → UniFi Protect
   Alarm Bridge**.
2. Select your existing Protect integration. No second password is required.
   Without an existing integration, enter the console address and dedicated
   account credentials. HTTPS certificate verification is always required:
   use a trusted certificate, or enter its SHA-256 fingerprint after verifying
   it through a trusted connection to your console. Never accept an unverified pin.
3. If you have more than one arm profile, choose which profile **Arm away**
   uses. **Arm home** and **Arm night** are optional.

You can change the mapping later under the integration's **Configure** button.

### Behaviour worth knowing

- **Arming from HA respects the profile's exit delay.** The panel shows
  `arming` until Protect reports `armed`.
- **Changing modes requires an explicit disarm first. Selecting another mode never automatically disarms the current one.**
- **Disarm refreshes the profile list and sends disarm to every profile, including those last reported as disarmed.**
- **External changes appear on the next poll (normally within 15 seconds in
  session reuse mode), or through the dedicated mode's websocket.** If a profile you haven't mapped is armed, the panel shows
  `armed_custom_bypass`, and its `profile_title` attribute names the profile.
- **If the official UniFi Protect integration is also installed, the alarm
  panel appears on the same console device** (both integrations identify it
  by its MAC address).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Entity **unavailable** | The console can't be reached, or the current state cannot be verified | Check the source Protect integration in session reuse mode; for a dedicated account, check **Settings → Repairs** |
| Repair: **account is not a Super Admin** | The account's role was changed | Give it the Super Admin role again |
| Repair: **not in Global mode** | Alarm Manager switched back to Local mode (e.g. after a firmware update) | Switch it to Global in Protect |
| Repair: **instant updates unavailable** | The websocket has been down for over an hour, usually after a firmware change | State still updates every 10 s; report it if it persists |
| Repair: **mapped profile no longer exists** | An arm profile was deleted or recreated | Click **Fix** and choose the profiles again |
| **Arm does nothing** | Wrong profile mapping, or the profile itself is misconfigured in Protect | Check **Configure**, then try arming the same profile from Protect |
| Setup error **two-factor** | The account has MFA | Use a local-only account without MFA |

When reporting a problem, attach **Download diagnostics** from the integration's
menu. Hostnames, credentials, and profile and console names are redacted.

## License

MIT
