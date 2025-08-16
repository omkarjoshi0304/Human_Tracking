# Real-Time Multi-Room Human Tracking (mmWave + MQTT + InfluxDB + Grafana)

**Privacy-preserving human presence & activity monitoring** across multiple rooms using **C1001 mmWave sensors** (ESP32), **MQTT**, **Telegraf**, **InfluxDB**, and **Grafana**.  
The system achieves **sub-second E2E latency**, **~95% presence accuracy**, and **real-time dashboards** with anomaly alerts.

> Live stack: ESP32 → MQTT → Telegraf → InfluxDB → Grafana

Python broker-side monitor & data generator


---

## ✨ Features

- Multi-room presence & movement classification (`walking/standing/sitting/none`)
- Real-time dashboards: status tiles, timelines, room usage bars, heatmaps
- Anomaly alerts (e.g., ALL ROOMS EMPTY, unusual/high activity)
- Validated data model (`measurement=human_tracking`) with clean tags & fields
- Lightweight, reproducible stack (local or edge device)

---

## 📁 Repository Structure

├── firmware/ # (optional) ESP32 sketches / notes
├── telegraf.conf # Telegraf MQTT → InfluxDB pipeline config
├── system_monitor.py # Python broker-side monitor & test data generator
├── Sensor_interface.* # (optional) sensor/edge helpers
├── dashboards/ # (optional) Grafana JSON exports
└── README.md # you are here


---

## 🧰 Prerequisites

- **Hardware**: ESP32-DevKitC + C1001 mmWave radar (×3 for Room/Hall/Kitchen)
- **OS**: Linux, macOS, or Windows
- **Software**
  - MQTT broker: **Eclipse Mosquitto**
  - **InfluxDB 2.x**
  - **Telegraf**
  - **Grafana**
  - **Python 3.9+** (for the broker monitor/generator)
- **Network**: ESP32 and server machine on the same LAN

---

## ⚡ Quick Start (TL;DR)

1. Install Mosquitto, InfluxDB 2.x, Telegraf, Grafana.  
2. Create InfluxDB **Org** and **Bucket**: `dcu masters project`.  
3. Put your **Influx token** into `telegraf.conf` and start Telegraf.  
4. Run `system_monitor.py` to publish guaranteed-schema test data and to watch live MQTT.  
5. Create a new Grafana dashboard and paste the **Flux queries** (below) for each panel.  
6. Watch presence, movement, heatmaps, and alerts in real time.

---

## 🛠️ Installation & Setup

### 1) Install core services

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
sudo apt install -y influxdb2 telegraf grafana
sudo systemctl enable --now mosquitto influxdb grafana-server

Windows

Install Mosquitto, InfluxDB2, Telegraf, Grafana from their official installers.

Start services from “Services” or each app’s tray/CLI.

2) InfluxDB 2.x bootstrap

Open InfluxDB UI (default http://localhost:8086) → complete onboarding:

Org: dcu masters project

Bucket: dcu masters project

Generate API Token and keep it handy.

3) Telegraf: MQTT → InfluxDB pipeline

Edit telegraf.conf (this repo) with your token and URL:

# Working Telegraf Configuration - Uses existing bucket
[agent]
  interval = "10s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "10s"
  flush_jitter = "0s"
  precision = ""
  hostname = ""
  omit_hostname = true

# MQTT Consumer
[[inputs.mqtt_consumer]]
  servers = ["tcp://localhost:1883"]
  
  # Your actual MQTT topics
  topics = [
    "home/sensors/Room/motion",
    "home/sensors/Hall/motion", 
    "home/sensors/Kitchen/motion",
    "home/status/Room",
    "home/status/Hall",
    "home/status/Kitchen",
    "home/sensors/+/motion",
    "home/status/+",
    "home/diagnostic/+",
    "home/events/+",
    "home/alerts/+"
  ]
  
  qos = 0
  connection_timeout = "30s"
  persistent_session = false
  client_id = "telegraf_working"
  
  # JSON parsing
  data_format = "json"
  json_time_key = "timestamp"
  json_time_format = "unix_ms"
  
  # Tags for better organization
  tag_keys = [
    "room",
    "sensor_type",
    "test_mode",
    "topic",
    "movement",
    "status",
    "raw_data",
    "presence",
    "event"
  ]
  
  # String fields
  json_string_fields = [
    "movement",
    "status",
    "raw_data",
    "event",
    "type",
    "test_mode",
    "presence"
  ]
  
  # Measurement name
  name_override = "human_tracking"

# InfluxDB v2 Output - Using your existing bucket
[[outputs.influxdb_v2]]
  urls = ["http://localhost:8086"]
  token = "I9n46TQ4cILlZ_yylb-o18KkaN_T0T0Kn53p-W80r32p98FdffZTb0d2iQ-IhshNAMo2cMrPRHM2rtF71J0tdA=="
  organization = "dcu masters project"
  bucket = "dcu masters project"  # Using your existing bucket
  timeout = "5s"

# Debug output to see what's being processed
[[outputs.file]]
  files = ["stdout"]
  data_format = "influx"

Start Telegraf:
telegraf --config telegraf.conf

MQTT broker check (optional)
# In another terminal
mosquitto_sub -h localhost -t "home/sensors/+motion"-v

Broker-side monitor & test data generator

This script publishes schema-correct JSON for Room, Hall, Kitchen and prints live summaries.

python3 system_monitor.py

Grafana: add InfluxDB data source

Open Grafana (http://localhost:3000, default admin/admin), add a Flux data source pointing to your InfluxDB:

URL: http://localhost:8086

Org: dcu masters project

Token: your token

Default bucket: dcu masters project

📊 Grafana Panels (Flux queries)

Create a new dashboard and add these 8 panels.
Note: Keep the bucket name exactly as below.

Panel 1 — 👤 Current Location

from(bucket: "dcu masters project")
  |> range(start: -3m)
  |> filter(fn: (r) => r._measurement == "human_tracking")
  |> filter(fn: (r) => r._field == "signal_strength")
  |> group(columns: ["room"])
  |> last()
  |> map(fn: (r) => ({
      room: r.room,
      status: if r.presence == "true" then "OCCUPIED" else "EMPTY",
      _value: if r.presence == "true" then 1 else 0
    }))
  |> sort(columns: ["_value"], desc: true)

Panel 2 — 🏠 Hall Status

from(bucket: "dcu masters project")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "human_tracking")
  |> filter(fn: (r) => r._field == "presence" or r._field == "movement" or r._field == "signal_strength")
  |> filter(fn: (r) => r.room == "Hall")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "room", "presence", "movement", "signal_strength"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 10)

Panel 3 — ⚡ Unusual Activity Alert

from(bucket: "dcu masters project")
  |> range(start: -10m)
  |> filter(fn: (r) => r._measurement == "human_tracking")
  |> filter(fn: (r) => r._field == "signal_strength")
  |> filter(fn: (r) => r.movement == "walking")
  |> group(columns: ["room"])
  |> count()
  |> map(fn: (r) => ({
      r with
      _value: if r._value > 10 then 2 else if r._value > 5 then 1 else 0,
      alert_type: "MOVEMENT_ACTIVITY",
      message: if r._value > 10 then "🔴 HIGH ACTIVITY IN " + r.room 
               else if r._value > 5 then "🟡 MODERATE ACTIVITY IN " + r.room 
               else "✅ NORMAL ACTIVITY IN " + r.room
    }))
  |> group()
  |> max()

Panel 4 — 🚶 Movement Activity Timeline

from(bucket: "dcu masters project")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "human_tracking")
  |> filter(fn: (r) => r["_field"] == "movement")
  |> map(fn: (r) => ({
      r with _value: 
        if r._value == "walking" then 4.0
        else if r._value == "standing" then 3.0
        else if r._value == "sitting" then 2.0
        else if r._value == "none" then 0.0
        else 1.0
    }))

Panel 5 — 🏠 All Rooms Empty Alert

from(bucket: "dcu masters project")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "human_tracking")
  |> filter(fn: (r) => r._field == "signal_strength")
  |> filter(fn: (r) => r.presence == "true")
  |> count()
  |> map(fn: (r) => ({
      r with
      _value: if r._value == 0 then 1 else 0,
      alert_type: "NO_PRESENCE",
      message: if r._value == 0 then "🚨 ALL ROOMS EMPTY" else "✅ ROOMS OCCUPIED"
    }))

Panel 6 — 📊 Room Usage Comparison

from(bucket: "dcu masters project")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r._measurement == "human_tracking")
  |> filter(fn: (r) => r._field == "signal_strength")
  |> group(columns: ["room"])
  |> mean()
  |> sort(columns: ["_value"], desc: true)

Panel 7 — 🏠 Kitchen Status

from(bucket: "dcu masters project")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "human_tracking")
  |> filter(fn: (r) => r._field == "presence" or r._field == "movement" or r._field == "signal_strength")
  |> filter(fn: (r) => r.room == "Kitchen")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "room", "presence", "movement", "signal_strength"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 10)

Panel 8 — 🔥 Daily Activity Heatmap

from(bucket: "dcu masters project")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "human_tracking")
  |> filter(fn: (r) => r["_field"] == "movement")
  |> map(fn: (r) => ({
      r with _value: 
        if r._value == "walking" then 4.0
        else if r._value == "standing" then 3.0
        else if r._value == "sitting" then 2.0
        else if r._value == "none" then 0.0
        else 1.0
    }))


