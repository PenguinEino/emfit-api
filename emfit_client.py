"""Emfit QS API client - wraps the undocumented qs-api.emfit.com endpoints."""

import httpx
from typing import Any

BASE_URL = "https://qs-api.emfit.com/api/v1"


class EmfitClient:
    def __init__(self, token: str | None = None):
        self._token = token
        self._http = httpx.Client(timeout=30)

    @property
    def _headers(self) -> dict[str, str]:
        if not self._token:
            raise RuntimeError("Not authenticated – call login() first")
        return {"Authorization": f"Bearer {self._token}"}

    # ── Auth ──────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Login and store JWT token. Returns user info + device settings."""
        resp = self._http.post(
            f"{BASE_URL}/login",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data.get("token")
        if not self._token:
            raise RuntimeError("Login succeeded but no token returned")
        return data

    def set_token(self, token: str) -> None:
        self._token = token

    # ── User ──────────────────────────────────────────────────────────

    def get_user(self) -> dict[str, Any]:
        """Get full user bundle (user, device_settings, notification_settings, token refresh)."""
        resp = self._http.get(f"{BASE_URL}/user/get", headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        # Each call returns a refreshed token
        if "token" in data:
            self._token = data["token"]
        return data

    def get_user_flat(self) -> dict[str, Any]:
        """Get user profile as a flat object (no device_settings bundle)."""
        resp = self._http.get(f"{BASE_URL}/user", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def update_user(self, payload: dict) -> dict[str, Any]:
        resp = self._http.put(f"{BASE_URL}/user", json=payload, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    # ── Device ────────────────────────────────────────────────────────

    def get_device(self, device_id: str) -> dict[str, Any]:
        resp = self._http.get(f"{BASE_URL}/device/{device_id}", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def update_device(self, payload: dict) -> dict[str, Any]:
        """Update device settings (name, timezone, night mode, etc.)."""
        resp = self._http.put(f"{BASE_URL}/device", json=payload, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_device_status(self, device_id: str) -> dict[str, Any]:
        resp = self._http.get(f"{BASE_URL}/device/status/{device_id}", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_device_status_all(self) -> dict[str, Any]:
        resp = self._http.get(f"{BASE_URL}/device/status/all", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_device_maintenance_status(self) -> dict[str, Any]:
        """Check device-level maintenance status."""
        resp = self._http.get(f"{BASE_URL}/device/status/maintenance", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_device_features(self, device_id: str) -> dict[str, Any]:
        resp = self._http.get(f"{BASE_URL}/device/features/{device_id}", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def update_device_features(self, device_id: str, payload: dict) -> dict[str, Any]:
        """Update device feature flags (naps, raw data, night mode, etc.)."""
        resp = self._http.put(
            f"{BASE_URL}/device/features/{device_id}", json=payload, headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    def get_notification_settings(self, device_id: str) -> dict[str, Any]:
        resp = self._http.get(
            f"{BASE_URL}/device/notification-settings/{device_id}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    def update_notification_settings(self, device_id: str, payload: dict) -> dict[str, Any]:
        """Update notification/alarm settings for a device."""
        resp = self._http.put(
            f"{BASE_URL}/device/notification-settings/{device_id}",
            json=payload,
            headers=self._headers,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Presence (sleep periods) ──────────────────────────────────────

    def get_presence_latest(self, device_id: str) -> dict[str, Any]:
        """Get the latest completed sleep period with all data (minitrends, time-series, etc.)."""
        resp = self._http.get(f"{BASE_URL}/presence/{device_id}/latest", headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        if "token" in data:
            self._token = data["token"]
        return data

    def get_presence(self, device_id: str, presence_id: str) -> dict[str, Any]:
        """Get a specific sleep period by its ID."""
        resp = self._http.get(
            f"{BASE_URL}/presence/{device_id}/{presence_id}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    def delete_presence(self, device_id: str, presence_id: str) -> dict[str, Any]:
        """Delete a sleep period."""
        resp = self._http.delete(
            f"{BASE_URL}/presence/{device_id}/{presence_id}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    def shorten_presence(self, presence_id: str, device_id: str, shorten_from: int, shorten_to: int) -> dict[str, Any]:
        """Trim/shorten a sleep period by adjusting its start or end time.

        Args:
            presence_id: MongoDB ObjectId of the sleep period
            device_id: device ID
            shorten_from: new start timestamp (Unix seconds)
            shorten_to: new end timestamp (Unix seconds)
        """
        payload = {
            "presence_id": presence_id,
            "device_id": device_id,
            "shorten_from": shorten_from,
            "shorten_to": shorten_to,
        }
        resp = self._http.post(
            f"{BASE_URL}/presence/shorten", json=payload, headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    def download_presence(self, presence_id: str) -> bytes:
        """Download sleep period data as CSV ZIP. Returns raw bytes."""
        resp = self._http.get(
            f"{BASE_URL}/presence/download/{presence_id}",
            params={"token": self._token},
        )
        resp.raise_for_status()
        return resp.content

    # ── Raw data (原信号) ─────────────────────────────────────────────

    def _raise_if_feature_disabled(self, resp: httpx.Response) -> None:
        if resp.status_code == 403:
            raise PermissionError(
                "Raw data feature is not enabled for this device (set enabled_raw=true in device features)"
            )

    def get_raw_periods(self, device_id: str) -> dict[str, Any]:
        """List available raw sensor data periods. Requires enabled_raw feature flag."""
        resp = self._http.get(f"{BASE_URL}/raw/{device_id}/list", headers=self._headers)
        self._raise_if_feature_disabled(resp)
        resp.raise_for_status()
        return resp.json()

    def get_raw_period(self, device_id: str, raw_period_id: str) -> dict[str, Any]:
        """Get raw sensor data for a specific period. Requires enabled_raw feature flag."""
        resp = self._http.get(
            f"{BASE_URL}/raw/{device_id}/{raw_period_id}", headers=self._headers
        )
        self._raise_if_feature_disabled(resp)
        resp.raise_for_status()
        return resp.json()

    def download_raw(self, device_id: str, raw_period_id: str, fmt: str = "csv") -> bytes:
        """Download raw sensor data as EDF or CSV file.

        Args:
            fmt: "csv" or "edf"
        """
        resp = self._http.get(
            f"{BASE_URL}/raw/download/{device_id}/{raw_period_id}/{fmt}",
            params={"token": self._token},
        )
        self._raise_if_feature_disabled(resp)
        resp.raise_for_status()
        return resp.content

    # ── Notes ─────────────────────────────────────────────────────────

    def create_note(self, presence_id: str, text: str, rating: int = 0) -> dict[str, Any]:
        """Create a note on a sleep period."""
        payload = {
            "presence_id": presence_id,
            "presence_object_id": presence_id,
            "text": text,
            "rating": rating,
        }
        resp = self._http.post(f"{BASE_URL}/note", json=payload, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def update_note(self, presence_id: str, text: str, rating: int = 0) -> dict[str, Any]:
        """Update an existing note on a sleep period."""
        payload = {
            "presence_id": presence_id,
            "presence_object_id": presence_id,
            "text": text,
            "rating": rating,
        }
        resp = self._http.put(f"{BASE_URL}/note", json=payload, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    # ── Trends ────────────────────────────────────────────────────────

    def get_trends(self, device_id: str, date_from: str, date_to: str) -> dict[str, Any]:
        """Get trend data. Dates in YYYY-MM-DD format."""
        resp = self._http.get(
            f"{BASE_URL}/trends/{device_id}/{date_from}/{date_to}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    # ── Timeline ──────────────────────────────────────────────────────

    def get_timeline(self, device_id: str, date_from: str, date_to: str) -> list[dict]:
        """Get timeline events. Dates in YYYY-MM-DD format."""
        resp = self._http.get(
            f"{BASE_URL}/timeline/{device_id}/{date_from}/{date_to}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    # ── Monitor (realtime) ────────────────────────────────────────────

    def get_monitor(self, device_id: str) -> dict[str, Any]:
        """Get realtime monitoring data (current heart rate, breathing, etc.)."""
        resp = self._http.get(f"{BASE_URL}/monitor/{device_id}", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_monitor_since(self, device_id: str, timestamp: int) -> dict[str, Any]:
        """Get incremental realtime data since a timestamp. For polling."""
        resp = self._http.get(
            f"{BASE_URL}/monitor/{device_id}/since/{timestamp}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    # ── Sync ──────────────────────────────────────────────────────────

    def get_sync_statuses(self, device_id: str) -> dict[str, Any]:
        """Get external service sync statuses (Validic, Wellmo, UACF, T-Peaks)."""
        resp = self._http.get(f"{BASE_URL}/sync/statuses/{device_id}", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    # ── Maintenance ───────────────────────────────────────────────────

    def get_maintenance(self) -> dict[str, Any]:
        """Check if the Emfit service is under maintenance."""
        resp = self._http.get(f"{BASE_URL}/auth/maintenance", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_maintenance_message(self) -> dict[str, Any]:
        """Get the current maintenance announcement message."""
        resp = self._http.get(f"{BASE_URL}/auth/maintenance/slave-message", headers=self._headers)
        resp.raise_for_status()
        if not resp.content.strip():
            return {"message": None}
        return resp.json()

    # ── Data export ───────────────────────────────────────────────────

    def request_export(self, device_id: str, date_from: int | None = None, date_to: int | None = None) -> dict[str, Any]:
        """Request a data export for a device.

        Args:
            date_from: start Unix timestamp (optional)
            date_to: end Unix timestamp (optional)
        """
        payload: dict[str, Any] = {"deviceId": device_id}
        if date_from is not None:
            payload["from"] = date_from
        if date_to is not None:
            payload["till"] = date_to
        resp = self._http.post(
            f"{BASE_URL}/export-data", json=payload, headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    def get_export_status(self, device_id: str) -> dict[str, Any]:
        """Check the status of a data export request."""
        resp = self._http.get(f"{BASE_URL}/export-data/{device_id}", headers=self._headers)
        resp.raise_for_status()
        # Returns empty body when no export has been requested
        if not resp.content.strip():
            return {"status": "no_export_requested"}
        return resp.json()

    def get_data_removal_status(self, device_id: str) -> dict[str, Any]:
        """Check the status of a device data deletion request."""
        resp = self._http.get(
            f"{BASE_URL}/check/remove/data/request/{device_id}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    # ── Paired devices ────────────────────────────────────────────────

    def get_paired_devices(self, device_id: str) -> dict[str, Any]:
        """List paired devices for a device."""
        resp = self._http.get(
            f"{BASE_URL}/paired-device/{device_id}/list", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._http.close()
