import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import yaml
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

sys.path.append(str(Path(".").resolve()))

from monitoring.alarms.alarm_engine import classify_status, process_alarm

MQTT_HOST = "localhost"
MQTT_PORT = 1883

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "stellarix-token"
INFLUX_ORG = "stellarix"
INFLUX_BUCKET = "datacenter"

TOPICS_FILE = Path("configs/mqtt_topics.yaml")

influx_client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = influx_client.write_api(write_options=SYNCHRONOUS)


def load_topics():
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["mqtt_topics"]


def normalize_state_status(value):
    value = str(value).upper()

    normal_states = [
        "NORMAL", "OK", "ACTIVE", "AVAILABLE", "AUTO",
        "UTILITY", "UTILITY SELECTED", "UTILITY: ON LOAD",
        "HEALTHY", "ONLINE", "ON LOAD"
    ]

    warning_states = [
        "WARNING", "ALARM", "LOW", "HIGH", "MANUAL"
    ]

    critical_states = [
        "CRITICAL", "FAULT", "FAILED", "OFFLINE",
        "TRIP", "EMERGENCY", "STOPPED"
    ]

    if value in normal_states:
        return "NORMAL"

    if value in warning_states:
        return "WARNING"

    if value in critical_states:
        return "CRITICAL"

    return "INFO"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ MQTT Collector connected")

        for item in load_topics():
            client.subscribe(item["topic"])

        print("✅ Subscribed to all MQTT topics")
    else:
        print(f"❌ MQTT connection failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        site = payload.get("site", "STELLARIX_DC01")
        system = payload.get("system", "unknown")
        zone = str(payload.get("zone", "none"))
        equipment = payload.get("equipment", "unknown")
        metric = payload.get("metric", "unknown")
        value = payload.get("value")

        base_point = (
            Point(system)
            .tag("site", site)
            .tag("zone", zone)
            .tag("equipment", equipment)
            .tag("metric", metric)
            .time(datetime.now(timezone.utc), WritePrecision.NS)
        )

        if isinstance(value, (int, float)):
            status = classify_status(system, metric, float(value))
            payload["status"] = status
            process_alarm(payload, status)

            point = (
                base_point
                .tag("status", status)
                .field("value", float(value))
                .field("value_type", "numeric")
            )

            write_api.write(
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
                record=point
            )

            print(f"✅ NUMERIC | {system} | {equipment} | {metric} = {value} | {status}")
            return

        state_value = str(value).upper()
        status = normalize_state_status(state_value)
        payload["status"] = status
        process_alarm(payload, status)

        point = (
            base_point
            .tag("status", status)
            .tag("state", state_value)
            .field("state_value", state_value)
            .field("value_type", "state")
        )

        write_api.write(
            bucket=INFLUX_BUCKET,
            org=INFLUX_ORG,
            record=point
        )

        print(f"✅ STATE   | {system} | {equipment} | {metric} = {state_value} | {status}")

    except Exception as e:
        print(f"❌ Error processing message: {e}")


def main():
    print("Starting OpenDC MQTT Collector + Alarm Engine → InfluxDB")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
