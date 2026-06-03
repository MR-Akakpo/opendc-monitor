import yaml
import json
import time
import random
from pathlib import Path
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

TOPICS_FILE = Path("configs/mqtt_topics.yaml")
MQTT_HOST = "localhost"
MQTT_PORT = 1883
PUBLISH_INTERVAL_SECONDS = 2

LEAD_GENERATOR = "GENERATOR_A"
LAG_GENERATOR = "GENERATOR_B"

def normal_value(system, equipment, metric):
    system = str(system).lower()
    equipment = str(equipment).upper()
    metric = str(metric).lower()

    # CHANGEOVER NORMAL STATE
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
                return "LEAD" if LEAD_GENERATOR == "GENERATOR_A" else "LAG"

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
                return "LEAD" if LEAD_GENERATOR == "GENERATOR_B" else "LAG"

        if equipment == "TCO_A":
            if metric == "status":
                return "NORMAL"
            if metric == "selected_source":
                return "UTILITY"
            if metric == "mode":
                return "AUTO"
            if metric == "lead_lag":
                return f"{LEAD_GENERATOR}=LEAD"
            if metric == "state":
                return "READY"
            if metric == "position":
                return "UTILITY"
            if metric == "input_1":
                return "UTILITY"
            if metric == "input_2":
                return LEAD_GENERATOR

        if equipment == "TCO_B":
            if metric == "status":
                return "NORMAL"
            if metric == "selected_source":
                return "TCO_A_OUTPUT"
            if metric == "mode":
                return "AUTO"
            if metric == "lead_lag":
                return f"{LAG_GENERATOR}=LAG"
            if metric == "state":
                return "READY"
            if metric == "position":
                return "TCO_A_OUTPUT"
            if metric == "input_1":
                return "TCO_A_OUTPUT"
            if metric == "input_2":
                return LAG_GENERATOR

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
                return 0
            if metric == "last_transfer":
                return "NO_RECENT_TRANSFER"
            if metric == "site_supply":
                return "SENELEC"
            if metric == "lead_generator":
                return LEAD_GENERATOR
            if metric == "lag_generator":
                return LAG_GENERATOR

    # VALEURS GENERALES POUR LES AUTRES MODULES
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

    if metric in ["dc_voltage"]:
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
    print("✅ Change Over normal mode: SENELEC priority, GEN A lead, GEN B lag")

    while True:
        for item in topics:
            value = normal_value(item["system"], item["equipment"], item["metric"])

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

        print(f"✅ Published {len(topics)} metrics | SUPPLY=SENELEC | LEAD={LEAD_GENERATOR} | LAG={LAG_GENERATOR}")
        time.sleep(PUBLISH_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
