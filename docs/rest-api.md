# Emfit QS REST API

Emfit QS 睡眠トラッカーのデータを取得するための REST API。
内部APIをラップし、整理されたエンドポイントを提供する。

## 基本情報

| 項目 | 値 |
|------|-----|
| Base URL | `http://localhost:8000` |
| レスポンス形式 | JSON |
| 認証 | サーバー起動時に環境変数で Emfit 認証情報を渡す (API 自体は認証不要) |
| ドキュメント (Swagger UI) | `http://localhost:8000/docs` |
| OpenAPI spec | `http://localhost:8000/openapi.json` |

### 起動方法

```bash
EMFIT_USERNAME=user@example.com EMFIT_PASSWORD=yourpassword python3 main.py
```

---

## エンドポイント一覧

### 便利エンドポイント (デバイスID自動検出)

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/status` | 現在の在床状態 |
| GET | `/api/sleep/latest` | 最新の睡眠データ (全量) |
| GET | `/api/sleep/latest/summary` | 最新の睡眠サマリー |

### 認証

| メソッド | パス | 説明 |
|---|---|---|
| POST | `/api/auth/login` | 再認証 |

### ユーザー

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/user` | ユーザー情報 |

### デバイス

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/devices` | デバイス一覧 |
| GET | `/api/device/{device_id}` | デバイス詳細 |
| GET | `/api/device/{device_id}/status` | 在床状態 |
| GET | `/api/device/{device_id}/features` | 機能フラグ |
| GET | `/api/device/{device_id}/notifications` | 通知設定 |

### 睡眠データ

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/device/{device_id}/sleep/latest` | 最新睡眠データ (全量) |
| GET | `/api/device/{device_id}/sleep/latest/summary` | 最新睡眠サマリー (整形済み) |
| GET | `/api/device/{device_id}/sleep/latest/timeseries` | 最新の時系列データ |
| GET | `/api/device/{device_id}/sleep/latest/minitrends` | 7日間ミニトレンド |
| GET | `/api/device/{device_id}/sleep/{presence_id}` | 特定の睡眠期間 |

### トレンド・タイムライン

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/device/{device_id}/trends` | 日次トレンドデータ |
| GET | `/api/device/{device_id}/timeline` | タイムラインイベント |

### リアルタイムモニター

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/device/{device_id}/monitor` | リアルタイムデータ |

---

## エンドポイント詳細

### GET `/api/status`

現在の在床状態をデバイスID自動検出で取得。

**レスポンス:**
```json
{
  "device_id": "1234",
  "device_name": "my-sleep-sensor",
  "firmware": "120.2.2.1",
  "presence": "absent",
  "since_timestamp": 1774397053000
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `device_id` | string | デバイスID |
| `device_name` | string | デバイス名 |
| `firmware` | string | ファームウェアバージョン |
| `presence` | string | `"present"` / `"absent"` / `"network-error"` / `"sensor-error"` / `"undeployed"` |
| `since_timestamp` | int | 状態変化時刻 (ミリ秒 UNIX タイムスタンプ) |

---

### POST `/api/auth/login`

**リクエスト:**
```json
{
  "username": "user@example.com",
  "password": "password"
}
```

**レスポンス:**
```json
{
  "status": "ok",
  "user": {
    "id": 12345,
    "username": "A1B2C3",
    "email": "user@example.com",
    "locale": "ja_JP",
    "timezone_id": 204,
    "gmt_offset": 32400,
    "devices": "1234",
    "time_format": "H24",
    "date_format": "MM-DD",
    "timezone_name": "Asia/Tokyo",
    "subscription": false,
    "verified_email": true
  },
  "devices": [
    {
      "device_id": "1234",
      "serial_number": "A1B2C3",
      "device_name": "my-sleep-sensor",
      "firmware": "120.2.2.1"
    }
  ]
}
```

---

### GET `/api/user`

**レスポンス:**
```json
{
  "user": {
    "id": 12345,
    "username": "A1B2C3",
    "email": "user@example.com",
    "locale": "ja_JP",
    "timezone_id": 204,
    "gmt_offset": 32400,
    "devices": "1234",
    "time_format": "H24",
    "date_format": "MM-DD",
    "timezone_name": "Asia/Tokyo",
    "subscription": false,
    "verified_email": true,
    "agreement": true,
    "consent": false
  },
  "device_settings": [ ... ],
  "notification_settings": { ... }
}
```

---

### GET `/api/devices`

**レスポンス:**
```json
{
  "devices": [
    {
      "device_id": "1234",
      "serial_number": "A1B2C3",
      "device_name": "my-sleep-sensor",
      "email": "user@example.com",
      "timezone_id": 204,
      "gmt_offset": 32400,
      "firmware": "120.2.2.1",
      "enabled_hrv": true,
      "enabled_naps": false,
      "enabled_raw": false,
      "enabled_raw_download": false,
      "enabled_night": false,
      "night_start": "2300",
      "night_end": "0700",
      "minitrend_days": 7,
      "has_fm": false
    }
  ]
}
```

---

### GET `/api/device/{device_id}`

**レスポンス:**
```json
{
  "device_name": "my-sleep-sensor",
  "firmware": "120.2.2.1",
  "field1": null,
  "field2": null
}
```

---

### GET `/api/device/{device_id}/status`

**レスポンス:**
```json
{
  "device_index": "1234",
  "description": "absent",
  "from": 1774397053000
}
```

---

### GET `/api/device/{device_id}/features`

**レスポンス:**
```json
{
  "enabled_naps": false,
  "minitrend_days": 7,
  "enabled_raw": false,
  "night_time": false,
  "night_time_start": null,
  "night_time_end": null,
  "fm": false,
  "fm_enable": false
}
```

---

### GET `/api/device/{device_id}/sleep/latest`

最新の睡眠データ全量。レスポンスは巨大 (時系列データを含む)。
フィールドの詳細は [内部APIリファレンス](emfit-qs-internal-api.md) の Presence セクションを参照。

---

### GET `/api/device/{device_id}/sleep/latest/summary`

時系列データを除いた睡眠サマリー。構造化済み。

**レスポンス:**
```json
{
  "id": "aabbccdd1122334455667788",
  "device_id": "1234",
  "time_start": 1774372980,
  "time_end": 1774397040,
  "from_utc": "2026-03-24 17:23:00",
  "to_utc": "2026-03-25 00:04:00",
  "time_duration": 24029,
  "sleep_score": 63,
  "sleep_score_2": 80,
  "sleep_duration": 20220,
  "sleep_efficiency": 87,
  "sleep_onset_duration": 2340,
  "sleep_awakenings": 1,
  "time_in_bed_duration": 23295,
  "sleep_stages": {
    "rem": { "duration": 4560, "percent": 23 },
    "light": { "duration": 11490, "percent": 57 },
    "deep": { "duration": 4170, "percent": 20 },
    "awake": { "duration": 3810, "percent": 16 }
  },
  "heart_rate": {
    "avg": 64,
    "min": 54,
    "max": 125
  },
  "respiratory_rate": {
    "avg": 14,
    "min": 7,
    "max": 22
  },
  "hrv": {
    "rmssd_avg": 40,
    "rmssd_min": 22.9,
    "rmssd_max": 107.7,
    "rmssd_evening": 27.7,
    "rmssd_morning": 52.7,
    "recovery_total": 25.1,
    "recovery_ratio": 1.91,
    "recovery_rate": 4.48,
    "recovery_integrated": 233,
    "lf": 45,
    "hf": 55
  },
  "movement": {
    "activity_avg": 159,
    "tossnturn_count": 79,
    "bed_exit_count": 2,
    "bed_exit_duration": 734
  },
  "note": null
}
```

| フィールド | 単位 | 説明 |
|---|---|---|
| `time_start` / `time_end` | 秒 (UNIX) | 睡眠期間の開始/終了 |
| `time_duration` | 秒 | 在床時間 |
| `sleep_score` | 0-100 | 睡眠スコア |
| `sleep_score_2` | 0-100 | 睡眠スコア (別アルゴリズム) |
| `sleep_duration` | 秒 | 実睡眠時間 |
| `sleep_efficiency` | % | 睡眠効率 (sleep_duration / time_in_bed_duration) |
| `sleep_onset_duration` | 秒 | 入眠にかかった時間 |
| `sleep_awakenings` | 回 | 中途覚醒回数 |
| `sleep_stages.*.duration` | 秒 | 各睡眠段階の時間 |
| `sleep_stages.*.percent` | % | 各睡眠段階の割合 |
| `heart_rate.*` | bpm | 心拍数 |
| `respiratory_rate.*` | 回/分 | 呼吸数 |
| `hrv.rmssd_*` | ms | 心拍変動 (RMSSD) |
| `hrv.recovery_total` | ms | HRV回復量 (朝 - 夕方) |
| `hrv.recovery_ratio` | 比率 | 回復比率 (朝 / 夕方) |
| `hrv.lf` / `hrv.hf` | % | 自律神経バランス (低周波/高周波) |
| `movement.activity_avg` | 任意単位 | 平均活動量 |
| `movement.tossnturn_count` | 回 | 寝返り回数 |
| `movement.bed_exit_count` | 回 | 離床回数 |
| `movement.bed_exit_duration` | 秒 | 離床合計時間 |

---

### GET `/api/device/{device_id}/sleep/latest/timeseries`

時系列データのみ。

**レスポンス:**
```json
{
  "id": "aabbccdd1122334455667788",
  "time_start": 1774372980,
  "time_end": 1774397040,
  "measured_datapoints": [
    [1774373026, null, null, 150],
    [1774373030, 62, 14, 148]
  ],
  "hrv_rmssd_datapoints": [
    [1774375476, 47, 27, 73, 0, 37]
  ],
  "sleep_epoch_datapoints": [
    [1774373040, 4],
    [1774373070, 3]
  ],
  "tossnturn_datapoints": [1774373038, 1774373070],
  "bed_exit_periods": [[1774397040, 1774396434]],
  "nodata_periods": []
}
```

| 配列 | 要素形式 | 間隔 | 説明 |
|---|---|---|---|
| `measured_datapoints` | `[timestamp, hr, rr, activity]` | ~4秒 | バイタルデータ。開始直後は hr/rr が null |
| `hrv_rmssd_datapoints` | `[timestamp, rmssd, lf, hf, 0, score]` | ~5分 | HRV時系列 |
| `sleep_epoch_datapoints` | `[timestamp, stage]` | 30秒 | 睡眠段階 (1=REM, 2=浅い, 3=深い, 4=覚醒) |
| `tossnturn_datapoints` | `timestamp` | 不定 | 寝返りイベント |
| `bed_exit_periods` | `[exit_ts, return_ts]` | 不定 | 離床期間 |

---

### GET `/api/device/{device_id}/sleep/latest/minitrends`

直近7日間のミニトレンド。

**レスポンス (抜粋):**
```json
{
  "minitrend_datestamps": [
    {"ts": 1773908624, "isWeekend": 0},
    {"ts": 1773995024, "isWeekend": 0}
  ],
  "minitrend_sleep_score": [68, 100, 95, 77, 100, 100, 52],
  "minitrend_sleep_efficiency": [92, 92, 88, 92, 90, 93, 85],
  "minitrend_sleep_duration": [5.95, 11.91, 8.8, 11.11, 8.61, 9.24, 7.27],
  "minitrend_measured_hr_avg": [68, 64, 62, 66, 65, 64, 65],
  "minitrend_measured_rr_avg": [15, 16, 15, 15, 15, 15, 16],
  "minitrend_hrv_rmssd_evening": [43, 43, 60, 44, 43, 43, 52],
  "minitrend_hrv_rmssd_morning": [53, 58, 61, 54, 48, 48, 41]
}
```

> 全31キーが返る。詳細は [内部APIリファレンス](emfit-qs-internal-api.md) の「7日間ミニトレンド」テーブルを参照。

---

### GET `/api/device/{device_id}/sleep/{presence_id}`

特定の睡眠期間を ID で取得。`navigation_data` 内の `id` フィールドで過去の睡眠期間を辿れる。

---

### GET `/api/device/{device_id}/trends`

日次集計のトレンドデータ。

**クエリパラメータ:**

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `date_from` | 30日前 | 開始日 (`YYYY-MM-DD`) |
| `date_to` | 今日 | 終了日 (`YYYY-MM-DD`) |

**レスポンス:**
```json
{
  "data": [
    {
      "date_ts": 1774224000,
      "date": "2026-03-23",
      "sleep_score": 100,
      "sleep_score_sma": 87.91,
      "sleep_duration": 8.61,
      "time_in_bed_duration": 9.55,
      "sleep_class_rem_duration": 1.83,
      "sleep_class_light_duration": 4.85,
      "sleep_class_deep_duration": 1.93,
      "sleep_class_awake_duration": 0.26,
      "meas_hr_avg": 64.9,
      "meas_hr_min": 49,
      "meas_hr_max": 88,
      "meas_rr_avg": 15.1,
      "meas_rr_min": 11.1,
      "meas_rr_max": 25.5,
      "meas_activity_avg": 337.6,
      "hrv_rmssd_evening": 37.4,
      "hrv_rmssd_morning": 61.2,
      "hrv_recovery_total": 23.8,
      "hrv_recovery_ratio": 1.64,
      "hrv_lf": 48,
      "hrv_hf": 52,
      "bed_exit_count": 2,
      "bed_exit_duration": 763,
      "tossnturn_count": 285
    }
  ],
  "gmt_offset": 32400,
  "sma_days": 7
}
```

> 各フィールドに `_sma` 接尾辞のバリアントあり (7日間移動平均)。
> duration 系の単位は**時間** (presence の秒とは異なる)。
> 全48フィールド/日。

---

### GET `/api/device/{device_id}/timeline`

**クエリパラメータ:**

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `date_from` | 7日前 | 開始日 (`YYYY-MM-DD`) |
| `date_to` | 今日 | 終了日 (`YYYY-MM-DD`) |

---

### GET `/api/device/{device_id}/monitor`

リアルタイムモニタリングデータ。在床時のみ有効なデータが返る。

**レスポンス (不在時):**
```json
{
  "measured_datapoints": [],
  "hrv_epochs": [],
  "device_id": "1234"
}
```

**レスポンス (在床時):**
```json
{
  "measured_datapoints": [
    [1774404626, 62, 15, 120],
    [1774404630, 63, 15, 95]
  ],
  "hrv_epochs": [
    [1774404500, 45, 30, 70, 0, 38]
  ],
  "device_id": "1234"
}
```

| 配列 | 要素形式 | 説明 |
|---|---|---|
| `measured_datapoints` | `[timestamp, hr, rr, activity]` | 現在のバイタルデータ |
| `hrv_epochs` | `[timestamp, rmssd, lf, hf, 0, score]` | 現在のHRVデータ |

---

## 在床状態の判定について

デバイスステータス API が返す `description` は以下の値のみ:

| 値 | 意味 |
|---|---|
| `present` | ベッドに人がいる (覚醒/睡眠の区別なし) |
| `absent` | ベッドに人がいない |
| `network-error` | デバイス通信断 |
| `sensor-error` | センサー異常 |
| `undeployed` | 初回データ未受信 |

**「在床+覚醒」と「在床+入眠」はリアルタイムでは直接区別できない。**
睡眠段階の判定 (`sleep_epoch_datapoints`) は睡眠期間の終了後にバッチ計算される。
