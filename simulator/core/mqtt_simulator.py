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
    default = {"lead_generator": "GENERATOR_A", "lag_generator": "GENERATOR_B", "transfer_time_seconds": 5}
    try:
        data = json.loads(CONTROL_FILE.read_text(encoding="utf-8"))
        lead = str(data.get("lead_generator", "GENERATOR_A")).upper()
        if lead not in ["GENERATOR_A", "GENERATOR_B"]:
            lead = "GENERATOR_A"
        lag = "GENERATOR_B" if lead == "GENERATOR_A" else "GENERATOR_A"
        return {"lead_generator": lead, "lag_generator": lag, "transfer_time_seconds": int(data.get("transfer_time_seconds", 5))}
    except Exception:
        return default

def value(system, equipment, metric, control):
    system = str(system).lower()
    equipment = str(equipment).upper()
    metric = str(metric).lower()

    lead = control["lead_generator"]
    lag = control["lag_generator"]

    if system == "changeover":
        if equipment == "UTILITY":
            return {
                "voltage": round(random.uniform(398, 404), 2),
                "frequency": round(random.uniform(49.97, 50.03), 2),
                "status": "ACTIVE",
                "available": "TRUE",
                "priority": "PRIORITY_1",
            }.get(metric, "NORMAL")

        if equipment == "GENERATOR_A":
            priority = "LEAD" if lead == "GENERATOR_A" else "LAG"
            rank = 2 if priority == "LEAD" else 3
            return {
                "voltage": round(random.uniform(398, 404), 2),
                "frequency": round(random.uniform(49.97, 50.03), 2),
                "status": "AVAILABLE",
                "available": "TRUE",
                "running": "FALSE",
                "on_load": "FALSE",
                "priority": priority,
                "priority_rank": rank,
            }.get(metric, "NORMAL")

        if equipment == "GENERATOR_B":
            priority = "LEAD" if lead == "GENERATOR_B" else "LAG"
            rank = 2 if priority == "LEAD" else 3
            return {
                "voltage": round(random.uniform(398, 404), 2),
                "frequency": round(random.uniform(49.97, 50.03), 2),
                "status": "AVAILABLE",
                "available": "TRUE",
                "running": "FALSE",
                "on_load": "FALSE",
                "priority": priority,
                "priority_rank": rank,
            }.get(metric, "NORMAL")

        if equipment == "TCO_A":
            return {
                "status": "NORMAL",
                "selected_source": "UTILITY",
                "mode": "AUTO",
                "lead_lag": f"{lead}=LEAD",
                "state": "READY",
                "position": "UTILITY",
                "input_1": "UTILITY",
                "input_2": "GENERATOR_A",
                "input_3": "GENERATOR_B",
                "source_1": "UTILITY",
                "source_2": "GENERATOR_A",
                "source_3": "GENERATOR_B",
                "output": "TGBT_A",
                "default_primary_backup": "GENERATOR_A",
                "default_secondary_backup": "GENERATOR_B",
                "effective_primary_backup": lead,
                "effective_secondary_backup": lag,
                "synchronized_with": "TCO_B",
            }.get(metric, "NORMAL")

        if equipment == "TCO_B":
            return {
                "status": "NORMAL",
                "selected_source": "UTILITY",
                "mode": "AUTO",
                "lead_lag": f"{lead}=LEAD",
                "state": "READY",
                "position": "UTILITY",
                "input_1": "UTILITY",
                "input_2": "GENERATOR_A",
                "input_3": "GENERATOR_B",
                "source_1": "UTILITY",
                "source_2": "GENERATOR_A",
                "source_3": "GENERATOR_B",
                "output": "TGBT_B",
                "default_primary_backup": "GENERATOR_B",
                "default_secondary_backup": "GENERATOR_A",
                "effective_primary_backup": lead,
                "effective_secondary_backup": lag,
                "synchronized_with": "TCO_A",
            }.get(metric, "NORMAL")

        if equipment == "ATS":
            return {
                "status": "NORMAL",
                "selected_source": "UTILITY",
                "mode": "AUTO",
                "transfer_state": "IDLE",
                "transfer_count": 0,
                "transfer_duration": control["transfer_time_seconds"],
                "last_transfer": "NO_RECENT_TRANSFER",
                "site_supply": "SENELEC",
                "lead_generator": lead,
                "lag_generator": lag,
            }.get(metric, "NORMAL")

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
    topics = yaml.safe_load(TOPICS_FILE.read_text(encoding="utf-8"))["mqtt_topics"]
    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    while True:
        control = read_control()
        for item in topics:
            payload = {
                "site": "STELLARIX_DC01",
                "system": item["system"],
                "zone": item.get("zone"),
                "equipment": item["equipment"],
                "metric": item["metric"],
                "value": value(item["system"], item["equipment"], item["metric"], control),
                "protocol": "simulated_iot_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            client.publish(item["topic"], json.dumps(payload))

        print(f"✅ Published {len(topics)} metrics | TCO A->TGBT_A | TCO B->TGBT_B | LEAD={control['lead_generator']} | LAG={control['lag_generator']}")
        time.sleep(PUBLISH_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
