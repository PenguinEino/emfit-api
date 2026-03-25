"""Emfit QS REST API – exposes all sleep tracking data from qs.emfit.com."""

import os
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel

from emfit_client import EmfitClient

# ── Configuration ─────────────────────────────────────────────────────

EMFIT_USERNAME = os.environ.get("EMFIT_USERNAME", "")
EMFIT_PASSWORD = os.environ.get("EMFIT_PASSWORD", "")

client: EmfitClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = EmfitClient()
    client.login(EMFIT_USERNAME, EMFIT_PASSWORD)
    yield
    if client:
        client.close()


app = FastAPI(
    title="Emfit QS API",
    description="REST API for Emfit QS sleep tracker data",
    version="1.0.0",
    lifespan=lifespan,
)


def get_client() -> EmfitClient:
    if client is None:
        raise HTTPException(503, "Client not initialized")
    return client


def get_device_id() -> str:
    """Get the first device ID from user info."""
    c = get_client()
    user_data = c.get_user()
    user = user_data.get("user", {})
    devices = user.get("devices", "")
    if not devices:
        raise HTTPException(404, "No devices found")
    return devices.split(",")[0].strip()


# ── Auth ──────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Authenticate and get a new session."""
    c = get_client()
    result = c.login(req.username, req.password)
    return {"status": "ok", "user": result.get("user"), "devices": result.get("device_settings")}


# ── User ──────────────────────────────────────────────────────────────


@app.get("/api/user")
def get_user():
    """Get current user profile."""
    c = get_client()
    data = c.get_user()
    return {
        "user": data.get("user"),
        "device_settings": data.get("device_settings"),
        "notification_settings": data.get("notification_settings"),
    }


@app.get("/api/user/profile")
def get_user_profile():
    """Get user profile as a flat object (no device_settings bundle)."""
    c = get_client()
    return c.get_user_flat()


@app.put("/api/user")
def update_user(payload: dict):
    """Update user settings (locale, timezone, date/time format, etc.)."""
    c = get_client()
    return c.update_user(payload)


# ── Device ────────────────────────────────────────────────────────────


@app.get("/api/devices")
def list_devices():
    """List all devices and their settings."""
    c = get_client()
    data = c.get_user()
    return {"devices": data.get("device_settings", [])}


@app.get("/api/devices/status")
def get_all_device_statuses():
    """Get presence status for all devices at once."""
    c = get_client()
    return c.get_device_status_all()


@app.get("/api/device/{device_id}")
def get_device(device_id: str):
    """Get device details (name, firmware, etc.)."""
    c = get_client()
    return c.get_device(device_id)


@app.put("/api/device/{device_id}")
def update_device(device_id: str, payload: dict):
    """Update device settings (name, timezone, night mode window, etc.).

    The payload is passed directly to the Emfit API. Common fields:
    - `device_name`: device display name
    - `gmt_offset`: timezone offset in seconds
    - `night_start` / `night_end`: night mode window (e.g. "2300", "0700")
    - `enabled_night`: enable/disable night mode
    """
    c = get_client()
    payload["device_id"] = device_id
    return c.update_device(payload)


@app.get("/api/device/{device_id}/status")
def get_device_status(device_id: str):
    """Get device status (present/absent on bed, last seen timestamp)."""
    c = get_client()
    return c.get_device_status(device_id)


@app.get("/api/device/{device_id}/features")
def get_device_features(device_id: str):
    """Get device feature flags (naps, raw data, night mode, etc.)."""
    c = get_client()
    return c.get_device_features(device_id)


@app.put("/api/device/{device_id}/features")
def update_device_features(device_id: str, payload: dict):
    """Update device feature flags.

    Common fields:
    - `enabled_naps`: enable nap tracking (bool)
    - `enabled_raw`: enable raw data recording (bool)
    - `enabled_night`: enable night mode (bool)
    - `night_time_start` / `night_time_end`: night window times
    """
    c = get_client()
    return c.update_device_features(device_id, payload)


@app.get("/api/device/{device_id}/notifications")
def get_notification_settings(device_id: str):
    """Get notification/alarm settings for device."""
    c = get_client()
    return c.get_notification_settings(device_id)


@app.put("/api/device/{device_id}/notifications")
def update_notification_settings(device_id: str, payload: dict):
    """Update notification/alarm settings for device.

    Common fields:
    - `alarm_profile`: alarm type ("off", "smart", "fixed")
    - `morning_alarm`: enable morning alarm (bool)
    - `morning_alarm_time`: alarm time (e.g. "07:00")
    - `afternoon_assurance`: enable afternoon assurance check (bool)
    - `evening_assurance`: enable evening assurance check (bool)
    - `sms_alert` / `email_alert`: enable alert channels (bool)
    - `enable_apnea`: enable apnea alerts (bool)
    """
    c = get_client()
    return c.update_notification_settings(device_id, payload)


@app.get("/api/device/{device_id}/sync/status")
def get_sync_statuses(device_id: str):
    """Get external service sync statuses (Wellmo, UACF, etc.)."""
    c = get_client()
    return c.get_sync_statuses(device_id)


@app.get("/api/device/{device_id}/paired-devices")
def get_paired_devices(device_id: str):
    """List paired devices associated with a device."""
    c = get_client()
    return c.get_paired_devices(device_id)


@app.get("/api/device/{device_id}/export/data-removal-status")
def get_data_removal_status(device_id: str):
    """Check the status of a pending device data deletion request."""
    c = get_client()
    return c.get_data_removal_status(device_id)


# ── Raw sensor data (原信号) ───────────────────────────────────────────


@app.get("/api/device/{device_id}/raw")
def get_raw_periods(device_id: str):
    """List available raw sensor data recording periods.

    Requires `enabled_raw` feature flag on the device.
    Each period has an `oid` (ID), `start`, and `end` timestamp.
    """
    c = get_client()
    try:
        return c.get_raw_periods(device_id)
    except PermissionError as e:
        raise HTTPException(403, str(e))


@app.get("/api/device/{device_id}/raw/{raw_period_id}/download")
def download_raw_data(
    device_id: str,
    raw_period_id: str,
    fmt: str = Query(default="csv", description="File format: 'csv' or 'edf'"),
):
    """Download raw sensor data for a recording period.

    Requires `enabled_raw` feature flag. Supports CSV and EDF formats.
    """
    c = get_client()
    try:
        data = c.download_raw(device_id, raw_period_id, fmt)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    media_type = "application/octet-stream" if fmt == "edf" else "text/csv"
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=raw_{raw_period_id}.{fmt}"},
    )


@app.get("/api/device/{device_id}/raw/{raw_period_id}")
def get_raw_period(device_id: str, raw_period_id: str):
    """Get raw sensor data for a specific recording period.

    Requires `enabled_raw` feature flag.
    Returns lo_band, hi_band, and integrated RR data arrays.
    """
    c = get_client()
    try:
        return c.get_raw_period(device_id, raw_period_id)
    except PermissionError as e:
        raise HTTPException(403, str(e))


# ── Presence (Sleep Periods) ──────────────────────────────────────────


@app.get("/api/device/{device_id}/sleep/latest")
def get_latest_sleep(device_id: str):
    """Get the latest (most recent) sleep period with full data.

    Returns:
    - Summary stats: sleep_score, sleep_duration, sleep_efficiency, etc.
    - Sleep stage breakdown: REM/light/deep durations and percentages
    - Vital signs summary: HR avg/min/max, RR avg/min/max, HRV (RMSSD)
    - HRV analysis: evening/morning RMSSD, recovery metrics, LF/HF balance
    - Time-series data: measured_datapoints (HR, RR, activity at ~4s intervals)
    - HRV time-series: hrv_rmssd_datapoints
    - Sleep epoch data: sleep_epoch_datapoints (sleep stage at 30s intervals)
    - Toss & turn events: tossnturn_datapoints
    - Bed exit periods: bed_exit_periods
    - 7-day minitrends for all metrics
    - Navigation data (links to nearby sleep periods)
    """
    c = get_client()
    return c.get_presence_latest(device_id)


@app.get("/api/device/{device_id}/sleep/{presence_id}/download")
def download_sleep_csv(device_id: str, presence_id: str):
    """Download a sleep period's raw data as CSV."""
    c = get_client()
    csv_bytes = c.download_presence(presence_id)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=sleep_{presence_id}.csv"},
    )


@app.get("/api/device/{device_id}/sleep/{presence_id}")
def get_sleep_period(device_id: str, presence_id: str):
    """Get a specific sleep period by its ID."""
    c = get_client()
    return c.get_presence(device_id, presence_id)


@app.delete("/api/device/{device_id}/sleep/{presence_id}")
def delete_sleep_period(device_id: str, presence_id: str):
    """Delete a sleep period permanently."""
    c = get_client()
    return c.delete_presence(device_id, presence_id)


class ShortenRequest(BaseModel):
    shorten_from: int
    shorten_to: int


@app.post("/api/device/{device_id}/sleep/{presence_id}/shorten")
def shorten_sleep_period(device_id: str, presence_id: str, req: ShortenRequest):
    """Trim/shorten a sleep period by adjusting its start or end time.

    Request body:
    - `shorten_from`: new start timestamp (Unix seconds)
    - `shorten_to`: new end timestamp (Unix seconds)
    """
    c = get_client()
    return c.shorten_presence(presence_id, device_id, req.shorten_from, req.shorten_to)


@app.get("/api/device/{device_id}/sleep/latest/summary")
def get_latest_sleep_summary(device_id: str):
    """Get a simplified summary of the latest sleep period (no time-series)."""
    c = get_client()
    data = c.get_presence_latest(device_id)

    return {
        "id": data.get("id"),
        "device_id": data.get("device_id"),
        "time_start": data.get("time_start"),
        "time_end": data.get("time_end"),
        "from_utc": data.get("from_utc"),
        "to_utc": data.get("to_utc"),
        "time_duration": data.get("time_duration"),
        "sleep_score": data.get("sleep_score"),
        "sleep_score_2": data.get("sleep_score_2"),
        "sleep_duration": data.get("sleep_duration"),
        "sleep_efficiency": data.get("sleep_efficiency"),
        "sleep_onset_duration": data.get("sleep_onset_duration"),
        "sleep_awakenings": data.get("sleep_awakenings"),
        "time_in_bed_duration": data.get("time_in_bed_duration"),
        "sleep_stages": {
            "rem": {
                "duration": data.get("sleep_class_rem_duration"),
                "percent": data.get("sleep_class_rem_percent"),
            },
            "light": {
                "duration": data.get("sleep_class_light_duration"),
                "percent": data.get("sleep_class_light_percent"),
            },
            "deep": {
                "duration": data.get("sleep_class_deep_duration"),
                "percent": data.get("sleep_class_deep_percent"),
            },
            "awake": {
                "duration": data.get("sleep_class_awake_duration"),
                "percent": data.get("sleep_class_awake_percent"),
            },
        },
        "heart_rate": {
            "avg": data.get("measured_hr_avg"),
            "min": data.get("measured_hr_min"),
            "max": data.get("measured_hr_max"),
        },
        "respiratory_rate": {
            "avg": data.get("measured_rr_avg"),
            "min": data.get("measured_rr_min"),
            "max": data.get("measured_rr_max"),
        },
        "hrv": {
            "rmssd_avg": data.get("measured_rmssd_avg"),
            "rmssd_min": data.get("measured_rmssd_min"),
            "rmssd_max": data.get("measured_rmssd_max"),
            "rmssd_evening": data.get("hrv_rmssd_evening"),
            "rmssd_morning": data.get("hrv_rmssd_morning"),
            "recovery_total": data.get("hrv_recovery_total"),
            "recovery_ratio": data.get("hrv_recovery_ratio"),
            "recovery_rate": data.get("hrv_recovery_rate"),
            "recovery_integrated": data.get("hrv_recovery_integrated"),
            "lf": data.get("hrv_lf"),
            "hf": data.get("hrv_hf"),
        },
        "movement": {
            "activity_avg": data.get("measured_activity_avg"),
            "tossnturn_count": data.get("tossnturn_count"),
            "bed_exit_count": data.get("bed_exit_count"),
            "bed_exit_duration": data.get("bed_exit_duration"),
        },
        "note": data.get("note"),
    }


@app.get("/api/device/{device_id}/sleep/latest/timeseries")
def get_latest_sleep_timeseries(device_id: str):
    """Get time-series data from the latest sleep period.

    - measured_datapoints: [[timestamp, hr, rr, activity], ...] at ~4s intervals
    - hrv_rmssd_datapoints: [[timestamp, rmssd, lf, hf, ...], ...]
    - sleep_epoch_datapoints: [[timestamp, stage], ...] at 30s intervals
      (stages: 1=REM, 2=light, 3=deep, 4=awake)
    - tossnturn_datapoints: [timestamp, ...] individual toss/turn events
    - bed_exit_periods: [[exit_ts, return_ts], ...] bed exit time ranges
    """
    c = get_client()
    data = c.get_presence_latest(device_id)

    return {
        "id": data.get("id"),
        "time_start": data.get("time_start"),
        "time_end": data.get("time_end"),
        "measured_datapoints": data.get("measured_datapoints"),
        "hrv_rmssd_datapoints": data.get("hrv_rmssd_datapoints"),
        "sleep_epoch_datapoints": data.get("sleep_epoch_datapoints"),
        "tossnturn_datapoints": data.get("tossnturn_datapoints"),
        "bed_exit_periods": data.get("bed_exit_periods"),
        "nodata_periods": data.get("nodata_periods"),
    }


@app.get("/api/device/{device_id}/sleep/latest/minitrends")
def get_latest_minitrends(device_id: str):
    """Get 7-day minitrend data from the latest sleep period."""
    c = get_client()
    data = c.get_presence_latest(device_id)

    minitrend_keys = [k for k in data if k.startswith("minitrend_")]
    return {k: data[k] for k in minitrend_keys}


# ── Notes ─────────────────────────────────────────────────────────────


class NoteRequest(BaseModel):
    presence_id: str
    text: str
    rating: int = 0


@app.post("/api/note")
def create_note(req: NoteRequest):
    """Create a text note on a sleep period."""
    c = get_client()
    return c.create_note(req.presence_id, req.text, req.rating)


@app.put("/api/note")
def update_note(req: NoteRequest):
    """Update an existing text note on a sleep period."""
    c = get_client()
    return c.update_note(req.presence_id, req.text, req.rating)


# ── Trends ────────────────────────────────────────────────────────────


@app.get("/api/device/{device_id}/trends")
def get_trends(
    device_id: str,
    date_from: str = Query(
        default=None, description="Start date (YYYY-MM-DD). Defaults to 30 days ago."
    ),
    date_to: str = Query(default=None, description="End date (YYYY-MM-DD). Defaults to today."),
):
    """Get trend data over a date range.

    Each day includes: sleep_score, sleep_duration, time_in_bed,
    sleep stage durations, HR/RR/activity stats, HRV metrics,
    bed exits, toss & turn count. Also includes SMA (simple moving average) variants.
    """
    c = get_client()
    if not date_to:
        date_to = date.today().isoformat()
    if not date_from:
        date_from = (date.today() - timedelta(days=30)).isoformat()
    return c.get_trends(device_id, date_from, date_to)


# ── Timeline ──────────────────────────────────────────────────────────


@app.get("/api/device/{device_id}/timeline")
def get_timeline(
    device_id: str,
    date_from: str = Query(
        default=None, description="Start date (YYYY-MM-DD). Defaults to 7 days ago."
    ),
    date_to: str = Query(default=None, description="End date (YYYY-MM-DD). Defaults to today."),
):
    """Get timeline events (presence/absence on bed over time)."""
    c = get_client()
    if not date_to:
        date_to = date.today().isoformat()
    if not date_from:
        date_from = (date.today() - timedelta(days=7)).isoformat()
    return c.get_timeline(device_id, date_from, date_to)


# ── Monitor (Realtime) ───────────────────────────────────────────────


@app.get("/api/device/{device_id}/monitor")
def get_monitor(device_id: str):
    """Get realtime monitoring data.

    Returns current measured_datapoints and HRV epochs.
    Data is available when a person is currently on the bed.
    """
    c = get_client()
    return c.get_monitor(device_id)


@app.get("/api/device/{device_id}/monitor/since/{timestamp}")
def get_monitor_since(device_id: str, timestamp: int):
    """Get incremental realtime monitoring data since a given timestamp.

    Use for polling: call this repeatedly with the last received timestamp
    to get only new data without re-fetching everything.

    - timestamp: Unix timestamp (seconds) of the last received datapoint
    """
    c = get_client()
    return c.get_monitor_since(device_id, timestamp)


# ── Maintenance ───────────────────────────────────────────────────────


@app.get("/api/maintenance")
def get_maintenance():
    """Check if the Emfit service is currently under maintenance."""
    c = get_client()
    return c.get_maintenance()


@app.get("/api/maintenance/message")
def get_maintenance_message():
    """Get the current maintenance announcement message (if any)."""
    c = get_client()
    return c.get_maintenance_message()


# ── Data Export ───────────────────────────────────────────────────────


class ExportRequest(BaseModel):
    date_from: int | None = None
    date_to: int | None = None


@app.post("/api/device/{device_id}/export")
def request_export(device_id: str, req: ExportRequest = ExportRequest()):
    """Request a data export for a device.

    Optional body:
    - `date_from`: start Unix timestamp
    - `date_to`: end Unix timestamp
    """
    c = get_client()
    return c.request_export(device_id, req.date_from, req.date_to)


@app.get("/api/device/{device_id}/export/status")
def get_export_status(device_id: str):
    """Check the status of a pending data export request."""
    c = get_client()
    return c.get_export_status(device_id)


# ── Convenience: auto-detect device ──────────────────────────────────


@app.get("/api/sleep/latest")
def get_latest_sleep_auto():
    """Get latest sleep data, auto-detecting the device ID."""
    device_id = get_device_id()
    return get_latest_sleep(device_id)


@app.get("/api/sleep/latest/summary")
def get_latest_sleep_summary_auto():
    """Get latest sleep summary, auto-detecting the device ID."""
    device_id = get_device_id()
    return get_latest_sleep_summary(device_id)


@app.get("/api/status")
def get_status_auto():
    """Get current bed presence status, auto-detecting the device ID."""
    device_id = get_device_id()
    c = get_client()
    status = c.get_device_status(device_id)
    device = c.get_device(device_id)
    return {
        "device_id": device_id,
        "device_name": device.get("device_name"),
        "firmware": device.get("firmware"),
        "presence": status.get("description"),
        "since_timestamp": status.get("from"),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
