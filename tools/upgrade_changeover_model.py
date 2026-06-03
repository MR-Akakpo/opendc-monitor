import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import yaml

MODEL = Path("configs/datacenter_model.yaml")
BACKUP_DIR = Path("configs/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

backup = BACKUP_DIR / f"datacenter_model_before_changeover_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
shutil.copy2(MODEL, backup)

with MODEL.open("r", encoding="utf-8") as f:
    model = yaml.safe_load(f)

systems = model.setdefault("systems", {})
changeover = systems.setdefault("changeover", {})
equipments = changeover.setdefault("equipments", {})

equipments["utility"] = {
    "label": "Utility Source",
    "metrics": {
        "voltage": "CHANGEOVER/UTILITY/voltage",
        "frequency": "CHANGEOVER/UTILITY/frequency",
        "status": "CHANGEOVER/UTILITY/status"
    }
}

equipments["generator_a"] = {
    "label": "Generator A Source",
    "metrics": {
        "voltage": "CHANGEOVER/GENERATOR_A/voltage",
        "frequency": "CHANGEOVER/GENERATOR_A/frequency",
        "status": "CHANGEOVER/GENERATOR_A/status",
        "available": "CHANGEOVER/GENERATOR_A/available",
        "on_load": "CHANGEOVER/GENERATOR_A/on_load"
    }
}

equipments["generator_b"] = {
    "label": "Generator B Source",
    "metrics": {
        "voltage": "CHANGEOVER/GENERATOR_B/voltage",
        "frequency": "CHANGEOVER/GENERATOR_B/frequency",
        "status": "CHANGEOVER/GENERATOR_B/status",
        "available": "CHANGEOVER/GENERATOR_B/available",
        "on_load": "CHANGEOVER/GENERATOR_B/on_load"
    }
}

equipments.setdefault("tco_a", {
    "label": "TCO A",
    "metrics": {}
})
equipments["tco_a"]["metrics"].update({
    "status": "CHANGEOVER/TCO_A/status",
    "selected_source": "CHANGEOVER/TCO_A/selected_source",
    "mode": "CHANGEOVER/TCO_A/mode",
    "lead_lag": "CHANGEOVER/TCO_A/lead_lag",
    "state": "CHANGEOVER/TCO_A/state"
})

equipments.setdefault("tco_b", {
    "label": "TCO B",
    "metrics": {}
})
equipments["tco_b"]["metrics"].update({
    "status": "CHANGEOVER/TCO_B/status",
    "selected_source": "CHANGEOVER/TCO_B/selected_source",
    "mode": "CHANGEOVER/TCO_B/mode",
    "lead_lag": "CHANGEOVER/TCO_B/lead_lag",
    "state": "CHANGEOVER/TCO_B/state"
})

equipments.setdefault("ats", {
    "label": "ATS",
    "metrics": {}
})
equipments["ats"]["metrics"].update({
    "status": "CHANGEOVER/ATS/status",
    "selected_source": "CHANGEOVER/ATS/selected_source",
    "mode": "CHANGEOVER/ATS/mode",
    "transfer_count": "CHANGEOVER/ATS/transfer_count",
    "transfer_duration": "CHANGEOVER/ATS/transfer_duration",
    "last_transfer": "CHANGEOVER/ATS/last_transfer",
    "transfer_state": "CHANGEOVER/ATS/transfer_state"
})

with MODEL.open("w", encoding="utf-8") as f:
    yaml.dump(model, f, sort_keys=False, allow_unicode=True)

print(f"✅ Backup créé: {backup}")
print("✅ Change Over model upgraded")

subprocess.run(["python", "deployment/scripts/generate_mqtt_topics.py"], check=True)

topics = yaml.safe_load(Path("configs/mqtt_topics.yaml").read_text(encoding="utf-8"))["mqtt_topics"]
changeover_topics = [t for t in topics if t["system"] == "changeover"]

print(f"✅ Total MQTT topics: {len(topics)}")
print(f"✅ Change Over topics: {len(changeover_topics)}")
for t in changeover_topics[:30]:
    print(" -", t["topic"])
