# Emfit QS 内部 API リファレンス

Emfit QS のフロントエンド (`qs.emfit.com`) が内部的に使用している REST API の仕様。
公式ドキュメントは存在しない。フロントエンド JS のリバースエンジニアリングにより特定。

## 基本情報

| 項目 | 値 |
|------|-----|
| Base URL | `https://qs-api.emfit.com/api/v1` |
| 認証方式 | JWT Bearer Token (`Authorization: Bearer <token>`) |
| レスポンス形式 | JSON |
| トークン有効期限 | 約7日 (604,800秒) |

> **注意**: `api-qs.emfit.com` という別ドメインも存在するが、JWT を返さないためAPIコールには使えない。`qs-api.emfit.com` を使用すること。

---

## 認証

### POST `/api/v1/login`

ログインして JWT トークンを取得する。

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
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9...",
  "remember_token": "$2y$10$...",
  "user": {
    "id": 12345,
    "username": "A1B2C3",
    "email": "user@example.com",
    "locale": "ja_JP",
    "timezone_id": 204,
    "gmt_offset": 32400,
    "devices": "1234",
    "field1": null,
    "field2": null,
    "time_format": "H24",
    "date_format": "MM-DD",
    "validic_user": null,
    "timezone_name": "Asia/Tokyo",
    "subscription": false,
    "verified_email": true,
    "agreement": true,
    "consent": false
  },
  "device_settings": [
    {
      "device_id": "1234",
      "serial_number": "A1B2C3",
      "device_name": "my-sleep-sensor",
      "firmware": "120.2.2.1",
      "gmt_offset": 32400,
      "enabled_hrv": true,
      "enabled_naps": false,
      "enabled_raw": false,
      "enabled_raw_download": false,
      "enabled_night": false,
      "night_start": "2300",
      "night_end": "0700",
      "minitrend_days": 7,
      "has_fm": false,
      "synced_wellmo": false,
      "synced_uacf": false,
      "synced_tpeaks": false
    }
  ],
  "notification_settings": {
    "1234": {
      "device_id": "1234",
      "sms_alert": false,
      "email_alert": false,
      "alarm_profile": "off",
      "morning_alarm": false,
      "morning_alarm_time": "07:00",
      "afternoon_assurance": false,
      "afternoon_assurance_duration": 6,
      "evening_assurance": false,
      "night_alarm_time": "21:00",
      "night_alarm_tolerance": 20,
      "night_alarm_bedreturn": true,
      "enable_apnea": false,
      "enable_fm": false
    }
  }
}
```

> 以降の全エンドポイントには `Authorization: Bearer <token>` ヘッダーが必要。
> 多くのエンドポイントがレスポンスに新しい `token` を含み、トークンが自動更新される。

---

## ユーザー

### GET `/api/v1/user/get`

現在のユーザー情報を取得。レスポンスには更新済みトークンも含まれる。

**レスポンス:** `login` と同じ構造 (`token`, `user`, `device_settings`, `notification_settings`)

### PUT `/api/v1/user`

ユーザー設定を更新。

---

## デバイス

### GET `/api/v1/device/{device_id}`

デバイスの基本情報。

**レスポンス:**
```json
{
  "field1": null,
  "field2": null,
  "device_name": "my-sleep-sensor",
  "firmware": "120.2.2.1"
}
```

### GET `/api/v1/device/status/{device_id}`

デバイスの現在の状態（在床 / 不在）。

**レスポンス:**
```json
{
  "device_index": "1234",
  "description": "absent",
  "from": 1774397053000
}
```

| `description` の値 | 意味 |
|---|---|
| `present` | ベッドに人がいる |
| `absent` | ベッドに人がいない |
| `network-error` | デバイスとの通信断 |
| `sensor-error` | センサー異常 |
| `undeployed` | 初回データ未受信 |

> `from` はミリ秒単位の UNIX タイムスタンプ。

### GET `/api/v1/device/status/all`

全デバイスのステータスを一括取得。

### GET `/api/v1/device/features/{device_id}`

デバイスの機能フラグ。

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

### GET `/api/v1/device/notification-settings/{device_id}`

デバイスの通知・アラーム設定。

**レスポンス:** `login` レスポンス内の `notification_settings` と同構造。

---

## 睡眠データ (Presence)

### GET `/api/v1/presence/{device_id}/latest`

最新の睡眠期間データ（全量）。最も情報量の多いエンドポイント。

### GET `/api/v1/presence/{device_id}/{presence_id}`

特定の睡眠期間を ID で取得。`navigation_data` 内の `id` を使用する。

**レスポンスの構造（全フィールド）:**

#### スカラー値（サマリー統計）

| フィールド | 型 | 例 | 説明 |
|---|---|---|---|
| `id` | string | `"aabbccdd1122334455667788"` | 睡眠期間の一意ID (MongoDB ObjectId) |
| `device_id` | int | `1234` | デバイスID |
| `time_start` | int | `1774372980` | 開始タイムスタンプ (秒) |
| `time_end` | int | `1774397040` | 終了タイムスタンプ (秒) |
| `time_duration` | int | `24029` | 総時間 (秒) |
| `from_utc` | string | `"2026-03-24 17:23:00"` | 開始時刻 (UTC) |
| `to_utc` | string | `"2026-03-25 00:04:00"` | 終了時刻 (UTC) |
| `time_start_string` | string | `"03/24 19:23"` | 開始時刻 (表示用) |
| `time_end_string` | string | `"02:04"` | 終了時刻 (表示用) |
| `time_user_gmt_offset` | int | `540` | ユーザーのGMTオフセット (分) |
| `time_start_gmt_offset` | int | `120` | データのGMTオフセット (分) |

#### 睡眠スコア・効率

| フィールド | 型 | 例 | 説明 |
|---|---|---|---|
| `sleep_score` | int | `63` | 睡眠スコア (0-100) |
| `sleep_score_2` | int | `80` | 睡眠スコア 2 (0-100、別アルゴリズム) |
| `sleep_efficiency` | int | `87` | 睡眠効率 (%) |
| `sleep_duration` | int | `20220` | 実睡眠時間 (秒) |
| `time_in_bed_duration` | int | `23295` | 在床時間 (秒) |
| `sleep_onset_duration` | int | `2340` | 入眠潜時 (秒) |
| `sleep_awakenings` | int | `1` | 中途覚醒回数 |

#### 睡眠段階

| フィールド | 型 | 例 | 説明 |
|---|---|---|---|
| `sleep_class_rem_duration` | int | `4560` | REM睡眠時間 (秒) |
| `sleep_class_rem_percent` | int | `23` | REM睡眠割合 (%) |
| `sleep_class_light_duration` | int | `11490` | 浅い睡眠時間 (秒) |
| `sleep_class_light_percent` | int | `57` | 浅い睡眠割合 (%) |
| `sleep_class_deep_duration` | int | `4170` | 深い睡眠時間 (秒) |
| `sleep_class_deep_percent` | int | `20` | 深い睡眠割合 (%) |
| `sleep_class_awake_duration` | int | `3810` | 覚醒時間 (秒) |
| `sleep_class_awake_percent` | int | `16` | 覚醒割合 (%) |

#### 心拍数 (HR)

| フィールド | 型 | 例 | 説明 |
|---|---|---|---|
| `measured_hr_avg` | int | `64` | 平均心拍数 (bpm) |
| `measured_hr_min` | int | `54` | 最低心拍数 (bpm) |
| `measured_hr_max` | int | `125` | 最高心拍数 (bpm) |

#### 呼吸数 (RR)

| フィールド | 型 | 例 | 説明 |
|---|---|---|---|
| `measured_rr_avg` | int | `14` | 平均呼吸数 (回/分) |
| `measured_rr_min` | int | `7` | 最低呼吸数 (回/分) |
| `measured_rr_max` | int | `22` | 最高呼吸数 (回/分) |

#### HRV (心拍変動)

| フィールド | 型 | 例 | 説明 |
|---|---|---|---|
| `measured_rmssd_avg` | int | `40` | 平均RMSSD (ms) |
| `measured_rmssd_min` | float | `22.9` | 最低RMSSD (ms) |
| `measured_rmssd_max` | float | `107.7` | 最高RMSSD (ms) |
| `hrv_rmssd_evening` | float | `27.7` | 夕方RMSSD (ms) |
| `hrv_rmssd_morning` | float | `52.7` | 朝RMSSD (ms) |
| `hrv_recovery_total` | float | `25.1` | 回復量 (morning - evening) |
| `hrv_recovery_ratio` | float | `1.91` | 回復比率 (morning / evening) |
| `hrv_recovery_rate` | float | `4.48` | 回復速度 |
| `hrv_recovery_integrated` | int | `233` | 統合回復指標 |
| `hrv_lf` | int | `45` | 低周波成分 (%) |
| `hrv_hf` | int | `55` | 高周波成分 (%) |
| `hrv_qual1` | int | `101` | HRVデータ品質1 |
| `hrv_qual2` | int | `71` | HRVデータ品質2 |

#### 体動

| フィールド | 型 | 例 | 説明 |
|---|---|---|---|
| `measured_activity_avg` | int | `159` | 平均活動量 |
| `tossnturn_count` | int | `79` | 寝返り回数 |
| `bed_exit_count` | int | `2` | 離床回数 |
| `bed_exit_duration` | int | `734` | 離床合計時間 (秒) |

#### その他

| フィールド | 型 | 例 | 説明 |
|---|---|---|---|
| `note` | string/null | `null` | ユーザーメモ |
| `snoring_data` | any/null | `null` | いびきデータ (対応デバイスのみ) |
| `system_nodata_periods` | bool | `false` | データ欠損期間の有無 |
| `object_id` | string | `"69c326a..."` | `id` と同一 |

#### 時系列データ (配列)

| フィールド | 要素数例 | 要素形式 | 説明 |
|---|---|---|---|
| `measured_datapoints` | 5836 | `[timestamp, hr, rr, activity]` | 約4秒間隔のバイタルデータ。hr/rr は計測開始直後は null |
| `hrv_rmssd_datapoints` | 81 | `[timestamp, rmssd, lf, hf, 0, score]` | HRV の時系列。約5分間隔 |
| `sleep_epoch_datapoints` | 801 | `[timestamp, stage]` | 30秒間隔の睡眠段階。stage: 1=REM, 2=light, 3=deep, 4=awake |
| `tossnturn_datapoints` | 79 | `timestamp` | 寝返りイベントのタイムスタンプ (秒) |
| `bed_exit_periods` | 2 | `[exit_ts, return_ts]` | 離床期間 [離床時刻, 復帰時刻] |
| `nodata_periods` | 0 | `[start_ts, end_ts]` | データ欠損期間 |
| `navigation_data` | 9 | オブジェクト (後述) | 近隣の睡眠期間へのリンク |

**`measured_datapoints` の例:**
```json
[[1774373026, null, null, 150], [1774373030, null, null, 113], [1774373034, 62, 14, 148]]
```

**`hrv_rmssd_datapoints` の例:**
```json
[[1774375476, 47, 27, 73, 0, 37], [1774376196, 43, 28, 72, 0, 38]]
```

**`sleep_epoch_datapoints` の例:**
```json
[[1774373040, 4], [1774373070, 4], [1774373100, 3]]
```
> stage 値: `1` = REM, `2` = 浅い睡眠, `3` = 深い睡眠, `4` = 覚醒

**`bed_exit_periods` の例:**
```json
[[1774397040, 1774396434], [1774373406, 1774373278]]
```

**`navigation_data` の例:**
```json
[
  {
    "id": "aabbccdd1122334455667788",
    "uid": 0,
    "date": "03/25 ",
    "weekday": "Wed",
    "dur": "6h 28",
    "duration_h": 6,
    "duration_m": 28
  }
]
```

#### 7日間ミニトレンド (配列、各7要素)

| フィールド | 例 (先頭3要素) | 説明 |
|---|---|---|
| `minitrend_datestamps` | `[{"ts":1773908624,"isWeekend":0}, ...]` | 日付タイムスタンプ |
| `minitrend_sleep_score` | `[68, 100, 95]` | 睡眠スコア |
| `minitrend_sleep_score_2` | `[64, 42, 100]` | 睡眠スコア2 |
| `minitrend_sleep_efficiency` | `[92, 92, 88]` | 睡眠効率 (%) |
| `minitrend_sleep_duration` | `[5.95, 11.91, 8.8]` | 睡眠時間 (時間) |
| `minitrend_time_in_bed_duration` | `[6.44, 12.97, 9.99]` | 在床時間 (時間) |
| `minitrend_sleep_class_in_rem_duration` | `[0.98, 3.46, 1.96]` | REM時間 (時間) |
| `minitrend_sleep_class_in_light_duration` | `[3.56, 5.97, 5.23]` | 浅い睡眠 (時間) |
| `minitrend_sleep_class_in_deep_duration` | `[1.41, 2.48, 1.61]` | 深い睡眠 (時間) |
| `minitrend_sleep_class_in_rem_percent` | `[17, 29, 22]` | REM割合 (%) |
| `minitrend_sleep_class_in_light_percent` | `[60, 50, 59]` | 浅い睡眠割合 (%) |
| `minitrend_sleep_class_in_deep_percent` | `[23, 21, 19]` | 深い睡眠割合 (%) |
| `minitrend_tossnturn_count` | `[82, 252, 257]` | 寝返り回数 |
| `minitrend_bedexit_count` | `[4, 4, 5]` | 離床回数 |
| `minitrend_measured_hr_avg` | `[68, 64, 62]` | 平均心拍 |
| `minitrend_measured_hr_max` | `[99, 79.7, 104.4]` | 最高心拍 |
| `minitrend_measured_hr_min` | `[42, 52, 44.4]` | 最低心拍 |
| `minitrend_measured_rr_avg` | `[15, 16, 15]` | 平均呼吸数 |
| `minitrend_measured_rr_min` | `[8.9, 9.3, 8.6]` | 最低呼吸数 |
| `minitrend_measured_rr_max` | `[23.8, 25.5, 25]` | 最高呼吸数 |
| `minitrend_measured_activity_avg` | `[184, 248, 278]` | 平均活動量 |
| `minitrend_hrv_rmssd_evening` | `[43, 43, 60]` | 夕方RMSSD |
| `minitrend_hrv_rmssd_morning` | `[53, 58, 61]` | 朝RMSSD |
| `minitrend_hrv_lf` | `[43, 44, 43]` | LF成分 (%) |
| `minitrend_hrv_recovery_total` | `[9.9, 14.4, 0.9]` | 回復量 |
| `minitrend_hrv_recovery_integrated` | `[228, 533, 342]` | 統合回復 |
| `minitrend_hrv_recovery_ratio` | `[1.23, 1.33, 1.01]` | 回復比率 |
| `minitrend_hrv_recovery_rate` | `[2.12, 1.4, null]` | 回復速度 |
| `minitrend_rmssd_min` | `[32.3, 21.8, 32.9]` | 最低RMSSD |
| `minitrend_rmssd_max` | `[73.2, 73, 93.2]` | 最高RMSSD |
| `minitrend_rmssd_avg` | `[48, 51, 61]` | 平均RMSSD |

### GET `/api/v1/presence/download/{presence_id}?token={token}`

睡眠データの CSV ダウンロード。クエリパラメータで token を渡す。

---

## トレンド

### GET `/api/v1/trends/{device_id}/{date_from}/{date_to}`

期間内の日次集計データ。日付は `YYYY-MM-DD` 形式。

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
      "sleep_duration_sma": 9.28,
      "time_in_bed_duration": 9.55,
      "time_in_bed_duration_sma": 10.2,
      "sleep_class_rem_duration": 1.83,
      "sleep_class_rem_duration_sma": 2.28,
      "sleep_class_light_duration": 4.85,
      "sleep_class_light_duration_sma": 5.13,
      "sleep_class_deep_duration": 1.93,
      "sleep_class_deep_duration_sma": 1.86,
      "sleep_class_awake_duration": 0.26,
      "sleep_class_awake_duration_sma": 0.47,
      "meas_hr_avg": 64.9,
      "meas_hr_avg_sma": 64.77,
      "meas_hr_min": 49,
      "meas_hr_min_sma": 47.58,
      "meas_hr_max": 88,
      "meas_hr_max_sma": 90.3,
      "meas_rr_avg": 15.1,
      "meas_rr_avg_sma": 15.17,
      "meas_rr_min": 11.1,
      "meas_rr_min_sma": 9.68,
      "meas_rr_max": 25.5,
      "meas_rr_max_sma": 24.65,
      "meas_activity_avg": 337.6,
      "meas_activity_avg_sma": 249.23,
      "hrv_rmssd_evening": 37.4,
      "hrv_rmssd_evening_sma": 50.61,
      "hrv_rmssd_morning": 61.2,
      "hrv_rmssd_morning_sma": 54.44,
      "hrv_recovery_total": 23.8,
      "hrv_recovery_total_sma": 12.25,
      "hrv_recovery_ratio": 1.64,
      "hrv_recovery_ratio_sma": 1.16,
      "hrv_lf": 48,
      "hrv_lf_sma": 46.03,
      "hrv_hf": 52,
      "hrv_hf_sma": 53.97,
      "bed_exit_count": 2,
      "bed_exit_count_sma": 3.2,
      "bed_exit_duration": 763,
      "bed_exit_duration_sma": 1283.6,
      "tossnturn_count": 285,
      "tossnturn_count_sma": 210.4
    }
  ],
  "gmt_offset": 32400,
  "sma_days": 7
}
```

> `_sma` 接尾辞のフィールドは 7日間の単純移動平均。
> `sleep_duration` / `time_in_bed_duration` / 各 `sleep_class_*_duration` の単位は**時間** (presence では秒だが、trends では時間)。

---

## タイムライン

### GET `/api/v1/timeline/{device_id}/{date_from}/{date_to}`

期間内の在床/不在イベントのリスト。日付は `YYYY-MM-DD` 形式。

---

## リアルタイムモニター

### GET `/api/v1/monitor/{device_id}`

現在のリアルタイムデータ。在床中 (`present`) のみ有効なデータが返る。

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

> `measured_datapoints` の形式: `[timestamp, hr, rr, activity]`
> `hrv_epochs` の形式: `[timestamp, rmssd, lf, hf, 0, score]`

### GET `/api/v1/monitor/{device_id}/since/{timestamp}`

指定タイムスタンプ以降の増分データを取得。ポーリング用。

---

## その他のエンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| POST | `/api/v1/user/register` | ユーザー登録 |
| POST | `/api/v1/device/add` | デバイス追加 |
| PUT | `/api/v1/device` | デバイス設定更新 |
| PUT | `/api/v1/device/notification-settings/{device_id}` | 通知設定更新 |
| PUT | `/api/v1/device/features/{device_id}` | 機能フラグ更新 |
| POST | `/api/v1/presence/shorten` | 睡眠期間の短縮 (トリミング) |
| DELETE | `/api/v1/presence/{device_id}/{presence_id}` | 睡眠期間の削除 |
| POST | `/api/v1/note` | メモ作成 |
| PUT | `/api/v1/note` | メモ更新 |
| POST | `/api/v1/iforgot` | パスワードリセット要求 |
| POST | `/api/v1/reset-password` | パスワードリセット実行 |
| POST | `/api/v1/device-verification` | デバイス認証 |
| GET | `/api/v1/email/verify/again` | メール再認証 |
| POST | `/api/v1/export-data` | データエクスポート要求 |
| GET | `/api/v1/export-data/{device_id}` | エクスポート状態確認 |
| POST | `/api/v1/device/remove/data` | デバイスデータ削除要求 |
| GET | `/api/v1/check/remove/data/request/{device_id}` | 削除状態確認 |
| GET | `/api/v1/remove/account` | アカウント削除要求 |
| GET | `/api/v1/check/remove/account/request` | 削除状態確認 |
| POST | `/api/v1/paired-device/add` | ペアリングデバイス追加 |
| DELETE | `/api/v1/paired-device/{id}` | ペアリングデバイス削除 |
| GET | `/api/v1/paired-device/{device_id}/list` | ペアリング一覧 |
| PUT | `/api/v1/paired-device/{id}` | ペアリングデバイス更新 |
| GET | `/api/v1/group/all` | グループ一覧 |
| POST | `/api/v1/group` | グループ作成 |
| PUT | `/api/v1/group/{id}` | グループ更新 |
| DELETE | `/api/v1/group/{id}` | グループ削除 |
| GET | `/api/v1/group-user/all` | グループユーザー一覧 |
| POST | `/api/v1/group-user` | グループユーザー追加 |
| POST | `/api/v1/group-device` | グループデバイス追加 |
| GET | `/api/v1/auth/maintenance` | メンテナンス状態確認 |
| GET | `/api/v1/auth/maintenance/slave-message` | メンテナンスメッセージ |
| GET | `/api/v1/sync/statuses/{device_id}` | 外部連携ステータス |
| POST | `/api/v1/consent/accepted` | 同意送信 |
