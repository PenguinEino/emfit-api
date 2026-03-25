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
        resp = self._http.get(f"{BASE_URL}/user/get", headers=self._headers)
        resp.raise_for_status()
        data = resp.json()
        # Each call returns a refreshed token
        if "token" in data:
            self._token = data["token"]
        return data

    def update_user(self, payload: dict) -> dict[str, Any]:
        resp = self._http.put(f"{BASE_URL}/user", json=payload, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    # ── Device ────────────────────────────────────────────────────────

    def get_device(self, device_id: str) -> dict[str, Any]:
        resp = self._http.get(f"{BASE_URL}/device/{device_id}", headers=self._headers)
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

    def get_device_features(self, device_id: str) -> dict[str, Any]:
        resp = self._http.get(f"{BASE_URL}/device/features/{device_id}", headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    def get_notification_settings(self, device_id: str) -> dict[str, Any]:
        resp = self._http.get(
            f"{BASE_URL}/device/notification-settings/{device_id}", headers=self._headers
        )
        resp.raise_for_status()
        return resp.json()

    # ── Presence (sleep periods) ──────────────────────────────────────

    def get_presence_latest(self, device_id: str) -> dict[str, Any]:
        """Get the latest sleep period with all data (minitrends, time-series, etc.)."""
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

    def close(self) -> None:
        self._http.close()
