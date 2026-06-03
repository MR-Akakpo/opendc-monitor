import yaml
import shutil
from pathlib import Path
from datetime import datetime

MODEL = Path("configs/datacenter_model.yaml")

if not MODEL.exists():
    MODEL.parent.mkdir(parents=True, exist_ok=True)

    MODEL.write_text(
"""
systems:
  environment:
    metrics: []
    zones: {}
""",
        encoding="utf-8",
    )

backup = Path(
    f"configs/backups/datacenter_model_before_environment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
)

shutil.copy2(MODEL, backup)

data = yaml.safe_load(MODEL.read_text(encoding="utf-8"))

if not data:
    data = {}

systems = data.setdefault("systems", {})
environment = systems.setdefault("environment", {})

environment["metrics"] = [
    "temperature",
    "humidity"
]

environment["zones"] = {

    "battery_room": {
        "label": "Battery Room",
        "sensors": [
            "A4",
            "A8",
            "A11",
            "B4",
            "B8",
            "B11"
        ]
    },

    "energy_centre": {
        "label": "Energy Centre",
        "sensors": [
            "A4",
            "A7",
            "A10",
            "B4",
            "B7",
            "B10"
        ]
    },

    "it_room": {
        "label": "IT Room",
        "sensors": [
            "A6","A11","A16",
            "B6","B11","B16",
            "C6","C11","C16",
            "D6","D11","D16",
            "E6","E11","E16",
            "F6","F11","F16",
            "G6","G11","G16",
            "H6","H11","H16"
        ]
    },

    "transmission_room": {
        "label": "Transmission Room",
        "sensors": [
            "A12",
            "A7",
            "B7"
        ]
    }
}

MODEL.write_text(
    yaml.dump(
        data,
        sort_keys=False,
        allow_unicode=True
    ),
    encoding="utf-8"
)

print()
print("===================================")
print("ENVIRONMENT SENSOR MODEL CREATED")
print("===================================")
print()

print("Metrics:")
print(" - Temperature")
print(" - Humidity")
print()

print("Battery Room : 6 sensors")
print("Energy Centre : 6 sensors")
print("IT Room : 24 sensors")
print("Transmission Room : 3 sensors")
print()

print("Total Sensors :", 39)
print("Total Metrics :", 78)
print()

print("Backup :", backup)
