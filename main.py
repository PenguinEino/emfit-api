"""Emfit QS REST API – exposes all sleep tracking data from qs.emfit.com."""

import os
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Query
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


# ── Device ────────────────────────────────────────────────────────────


@app.get("/api/devices")
def list_devices():
    """List all devices and their settings."""
    c = get_client()
    data = c.get_user()
    return {"devices": data.get("device_settings", [])}


@app.get("/api/device/{device_id}")
def get_device(device_id: str):
    """Get device details (name, firmware, etc.)."""
    c = get_client()
    return c.get_device(device_id)


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


@app.get("/api/device/{device_id}/notifications")
def get_notification_settings(device_id: str):
    """Get notification/alarm settings for device."""
    c = get_client()
    return c.get_notification_settings(device_id)


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


@app.get("/api/device/{device_id}/sleep/{presence_id}")
def get_sleep_period(device_id: str, presence_id: str):
    """Get a specific sleep period by its ID."""
    c = get_client()
    return c.get_presence(device_id, presence_id)


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
