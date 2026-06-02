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


def build_power_state():
    utility_ok = random.random() > 0.04
    gen_a_ok = random.random() > 0.08
    gen_b_ok = random.random() > 0.08

    if utility_ok:
        selected = "UTILITY"
        gen_a_status = "AVAILABLE" if gen_a_ok else "WARNING"
        gen_b_status = "AVAILABLE" if gen_b_ok else "WARNING"
    elif gen_a_ok:
        selected = "GENERATOR_A"
        gen_a_status = "ON_LOAD"
        gen_b_status = "AVAILABLE" if gen_b_ok else "WARNING"
    elif gen_b_ok:
        selected = "GENERATOR_B"
        gen_a_status = "WARNING"
        gen_b_status = "ON_LOAD"
    else:
        selected = "NO_SOURCE"
        gen_a_status = "FAULT"
        gen_b_status = "FAULT"

    return {
        "utility_ok": utility_ok,
        "gen_a_ok": gen_a_ok,
        "gen_b_ok": gen_b_ok,
        "selected_source": selected,
        "utility_status": "ACTIVE" if utility_ok else "FAILED",
        "gen_a_status": gen_a_status,
        "gen_b_status": gen_b_status,
        "ats_status": "NORMAL" if selected != "NO_SOURCE" else "CRITICAL",
        "ats_mode": "AUTO",
    }


def generate_value(system, equipment, metric, state):
    metric = str(metric).lower()
    equipment = str(equipment).upper()

    if metric == "selected_source":
        return state["selected_source"]

    if metric == "mode":
        return state["ats_mode"]

    if metric == "status":
        if equipment in ["ATS", "TCO_A", "TCO_B"]:
            return state["ats_status"]
        if "GENERATOR_A" in equipment:
            return state["gen_a_status"]
        if "GENERATOR_B" in equipment:
            return state["gen_b_status"]
        if "UTILITY" in equipment:
            return state["utility_status"]
        return random.choice(["NORMAL", "NORMAL", "NORMAL", "WARNING"])

    if metric == "bypass_status":
        return random.choice(["OFF", "OFF", "NORMAL"])

    if metric in ["voltage", "input_voltage", "output_voltage"]:
        if "GENERATOR_A" in equipment and state["selected_source"] == "GENERATOR_A":
            return round(random.uniform(398, 404), 2)
        if "GENERATOR_B" in equipment and state["selected_source"] == "GENERATOR_B":
            return round(random.uniform(398, 404), 2)
        if "UTILITY" in equipment and not state["utility_ok"]:
            return round(random.uniform(0, 50), 2)
        return round(random.uniform(390, 410), 2)

    if metric == "frequency":
        if "UTILITY" in equipment and not state["utility_ok"]:
            return 0
        return round(random.uniform(49.95, 50.05), 2)

    if metric in ["supply_temperature"]:
        return round(random.uniform(16, 21), 2)

    if metric in ["return_temperature", "temperature"]:
        return round(random.uniform(22, 28), 2)

    if metric in ["humidity", "return_humidity"]:
        return round(random.uniform(40, 58), 2)

    if metric in ["level", "level_fill", "fuel_level", "soc", "battery_soc"]:
        return round(random.uniform(70, 96), 2)

    if metric == "capacity":
        return round(random.uniform(8000, 20000), 2)

    if metric in ["dc_voltage"]:
        return round(random.uniform(51, 55), 2)

    if metric in ["current", "input_current", "output_current", "dc_current"]:
        return round(random.uniform(50, 500), 2)

    if metric in ["power", "load_kw", "total_load_kw"]:
        return round(random.uniform(250, 380), 2)

    if metric in ["load", "load_percent"]:
        return round(random.uniform(35, 75), 2)

    if metric == "power_factor":
        return round(random.uniform(0.92, 0.99), 2)

    if metric == "energy":
        return round(random.uniform(10000, 50000), 2)

    if metric == "pue":
        return round(random.uniform(1.35, 1.48), 2)

    if metric == "runtime_minutes":
        return round(random.uniform(20, 60), 2)

    return round(random.uniform(0, 100), 2)


def main():
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    topics = data["mqtt_topics"]

    client = mqtt.Client()
    client.connect(MQTT_HOST, MQTT_PORT, 60)

    print(f"✅ Connected to MQTT broker {MQTT_HOST}:{MQTT_PORT}")
    print(f"✅ Publishing to {len(topics)} topics...")

    while True:
        state = build_power_state()

        for item in topics:
            value = generate_value(
                item["system"],
                item["equipment"],
                item["metric"],
                state
            )

            payload = {
                "site": "STELLARIX_DC01",
                "system": item["system"],
                "zone": item.get("zone"),
                "equipment": item["equipment"],
                "metric": item["metric"],
                "value": value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            client.publish(item["topic"], json.dumps(payload))

        print(
            f"✅ Published {len(topics)} measurements | "
            f"ATS SOURCE = {state['selected_source']} | "
            f"UTILITY = {state['utility_status']} | "
            f"GEN A = {state['gen_a_status']} | "
            f"GEN B = {state['gen_b_status']}"
        )

        time.sleep(5)


if __name__ == "__main__":
    main()
