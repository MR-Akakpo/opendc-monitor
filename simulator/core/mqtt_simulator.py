import yaml
import json
import time
import random
from pathlib import Path
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

TOPICS_FILE = Path("configs/mqtt_topics.yaml")
CONTROL_FILE = Path("platform/backend/runtime/changeover_control.json")

MQTT_HOST = "localhost"
MQTT_PORT = 1883
PUBLISH_INTERVAL_SECONDS = 2


def read_control():
    default = {
        "lead_generator": "GENERATOR_A",
        "lag_generator": "GENERATOR_B",
        "transfer_time_seconds": 5
    }

    try:
        if CONTROL_FILE.exists():
            data = json.loads(CONTROL_FILE.read_text(encoding="utf-8"))
            lead = str(data.get("lead_generator", "GENERATOR_A")).upper()
            if lead not in ["GENERATOR_A", "GENERATOR_B"]:
                lead = "GENERATOR_A"

            lag = "GENERATOR_B" if lead == "GENERATOR_A" else "GENERATOR_A"

            return {
                "lead_generator": lead,
                "lag_generator": lag,
                "transfer_time_seconds": int(data.get("transfer_time_seconds", 5))
            }
    except Exception:
        pass

    return default


def normal_value(system, equipment, metric, control):
    system = str(system).lower()
    equipment = str(equipment).upper()
    metric = str(metric).lower()

    lead = control["lead_generator"]
    lag = control["lag_generator"]
    transfer_time = control["transfer_time_seconds"]

    if system == "changeover":
        if equipment == "UTILITY":
            if metric == "voltage":
                return round(random.uniform(398, 404), 2)
            if metric == "frequency":
                return round(random.uniform(49.97, 50.03), 2)
            if metric == "status":
                return "ACTIVE"
            if metric == "available":
                return "TRUE"
            if metric == "priority":
                return "PRIORITY_1"

        if equipment == "GENERATOR_A":
            if metric == "voltage":
                return round(random.uniform(398, 404), 2)
            if metric == "frequency":
                return round(random.uniform(49.97, 50.03), 2)
            if metric == "status":
                return "AVAILABLE"
            if metric == "available":
                return "TRUE"
            if metric == "running":
                return "FALSE"
            if metric == "on_load":
                return "FALSE"
            if metric == "priority":
                return "LEAD" if lead == "GENERATOR_A" else "LAG"

        if equipment == "GENERATOR_B":
            if metric == "voltage":
                return round(random.uniform(398, 404), 2)
            if metric == "frequency":
                return round(random.uniform(49.97, 50.03), 2)
            if metric == "status":
                return "AVAILABLE"
            if metric == "available":
                return "TRUE"
            if metric == "running":
                return "FALSE"
            if metric == "on_load":
                return "FALSE"
            if metric == "priority":
                return "LEAD" if lead == "GENERATOR_B" else "LAG"

        if equipment == "TCO_A":
            if metric == "status":
                return "NORMAL"
            if metric == "selected_source":
                return "UTILITY"
            if metric == "mode":
                return "AUTO"
            if metric == "lead_lag":
                return f"{lead}=LEAD"
            if metric == "state":
                return "READY"
            if metric == "position":
                return "UTILITY"
            if metric == "input_1":
                return "UTILITY"
            if metric == "input_2":
                return lead

        if equipment == "TCO_B":
            if metric == "status":
                return "NORMAL"
            if metric == "selected_source":
                return "TCO_A_OUTPUT"
            if metric == "mode":
                return "AUTO"
            if metric == "lead_lag":
                return f"{lag}=LAG"
            if metric == "state":
                return "READY"
            if metric == "position":
                return "TCO_A_OUTPUT"
            if metric == "input_1":
                return "TCO_A_OUTPUT"
            if metric == "input_2":
                return lag

        if equipment == "ATS":
            if metric == "status":
                return "NORMAL"
            if metric == "selected_source":
                return "UTILITY"
            if metric == "mode":
                return "AUTO"
            if metric == "transfer_state":
                return "IDLE"
            if metric == "transfer_count":
                return 0
            if metric == "transfer_duration":
                return transfer_time
            if metric == "last_transfer":
                return "NO_RECENT_TRANSFER"
            if metric == "site_supply":
                return "SENELEC"
            if metric == "lead_generator":
                return lead
            if metric == "lag_generator":
                return lag

    if metric in ["status", "bypass_status"]:
        return "NORMAL"
    if metric in ["voltage", "input_voltage", "output_voltage"]:
        return round(random.uniform(398, 404), 2)
    if metric == "frequency":
        return round(random.uniform(49.97, 50.03), 2)
    if metric in ["current", "input_current", "output_current", "dc_current"]:
        return round(random.uniform(120, 650), 2)
    if metric in ["power", "load_kw", "total_load_kw"]:
        return round(random.uniform(120, 380), 2)
    if metric in ["load", "load_percent"]:
        return round(random.uniform(42, 72), 2)
    if metric == "dc_voltage":
        return round(random.uniform(52.8, 54.5), 2)
    if metric in ["soc", "battery_soc", "level", "level_fill"]:
        return round(random.uniform(75, 96), 2)
    if metric == "capacity":
        return 20000 if "BULK" in equipment else 1000
    if metric in ["temperature", "return_temperature"]:
        return round(random.uniform(22, 28), 2)
    if metric == "supply_temperature":
        return round(random.uniform(16, 20), 2)
    if metric in ["humidity", "return_humidity"]:
        return round(random.uniform(40, 58), 2)
    if metric == "power_factor":
        return round(random.uniform(0.92, 0.99), 2)
    if metric == "energy":
        return round(random.uniform(10000, 50000), 2)
    if metric == "runtime_minutes":
        return round(random.uniform(25, 60), 2)
    if metric in ["active_critical", "active_warning", "total_active"]:
        return 0
    if metric == "last_alarm":
        return "NONE"

    return round(random.uniform(0, 100), 2)


def main():
    data = yaml.safe_load(TOPICS_FILE.read_text(encoding="utf-8"))
    topics = data["mqtt_topics"]

    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    print(f"✅ MQTT connected {MQTT_HOST}:{MQTT_PORT}")
    print(f"✅ Publishing {len(topics)} metrics every {PUBLISH_INTERVAL_SECONDS}s")
    print("✅ Simulator synchronized with changeover_control.json")

    while True:
        control = read_control()

        for item in topics:
            value = normal_value(
                item["system"],
                item["equipment"],
                item["metric"],
                control
            )

            payload = {
                "site": "STELLARIX_DC01",
                "system": item["system"],
                "zone": item.get("zone"),
                "equipment": item["equipment"],
                "metric": item["metric"],
                "value": value,
                "protocol": "simulated_iot_ready",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            client.publish(item["topic"], json.dumps(payload))

        print(
            f"✅ Published {len(topics)} metrics | "
            f"SUPPLY=SENELEC | "
            f"LEAD={control['lead_generator']} | "
            f"LAG={control['lag_generator']} | "
            f"TRANSFER_TIME={control['transfer_time_seconds']}s"
        )

        time.sleep(PUBLISH_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
