import yaml
from pathlib import Path

model_path = Path("configs/datacenter_model.yaml")
output_path = Path("configs/mqtt_topics.yaml")

BASE_TOPIC = "stellarix/stellarix_dc01"

def add_topic(topics, system, equipment, metric, topic, zone=None):
    topic = topic.strip("/")
    full_topic = f"{BASE_TOPIC}/{topic}".lower()

    item = {
        "system": system,
        "equipment": equipment,
        "metric": metric,
        "topic": full_topic
    }

    if zone:
        item["zone"] = zone

    topics.append(item)

def main():
    with open(model_path, "r", encoding="utf-8") as f:
        model = yaml.safe_load(f)

    topics = []
    systems = model["systems"]

    # CHANGEOVER
    for equipment, data in systems["changeover"]["equipments"].items():
        for metric, topic in data["metrics"].items():
            add_topic(topics, "changeover", equipment.upper(), metric, topic)

    # ENVIRONMENT
    env = systems["environment"]
    for zone, rooms in env["rooms"].items():
        for room in rooms:
            for metric, cfg in env["metrics"].items():
                topic = cfg["topic_template"].replace("{room}", room)
                add_topic(topics, "environment", room, metric, topic, zone)

    # FUEL
    for equipment, data in systems["fuel"]["equipments"].items():
        for metric, topic in data["metrics"].items():
            add_topic(topics, "fuel", equipment.upper(), metric, topic)

    # HVAC
    hvac = systems["hvac"]
    for group, equipments in hvac["equipments"].items():
        for equipment in equipments:
            for metric, cfg in hvac["metrics"].items():
                topic = cfg["topic_template"].replace("{equipment}", equipment)
                add_topic(topics, "hvac", equipment, metric, topic, group)

    # POWER METER
    power = systems["power_meter"]
    for group, equipments in power["equipments"].items():
        for equipment in equipments:
            for metric, cfg in power["metrics"].items():
                topic = cfg["topic_template"].replace("{equipment}", equipment)
                add_topic(topics, "power_meter", equipment, metric, topic, group)

    # RECTIFIER
    for equipment, data in systems["rectifier"]["equipments"].items():
        for metric, topic in data["metrics"].items():
            add_topic(topics, "rectifier", equipment.upper(), metric, topic)

    # UPS
    for equipment, data in systems["ups"]["equipments"].items():
        for metric, topic in data["metrics"].items():
            add_topic(topics, "ups", equipment.upper(), metric, topic)

    # BATTERY
    for equipment, data in systems["battery"]["equipments"].items():
        for metric, topic in data["metrics"].items():
            add_topic(topics, "battery", equipment.upper(), metric, topic)

    # ALARMS
    for metric, topic in systems["alarms"]["metrics"].items():
        add_topic(topics, "alarms", "ALARMS", metric, topic)

    # Remove duplicates
    unique = {}
    for item in topics:
        unique[item["topic"]] = item

    topics = list(unique.values())

    output = {"mqtt_topics": topics}

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, sort_keys=False, allow_unicode=True)

    print(f"✅ MQTT topics generated from datacenter_model.yaml: {output_path}")
    print(f"✅ Total topics: {len(topics)}")

if __name__ == "__main__":
    main()
