import yaml
from pathlib import Path

MODEL = Path("configs/datacenter_model.yaml")
data = yaml.safe_load(MODEL.read_text(encoding="utf-8"))

env = data["systems"]["environment"]

env["metrics"] = {
    "temperature": {
        "unit": "°C",
        "type": "numeric"
    },
    "humidity": {
        "unit": "%",
        "type": "numeric"
    }
}

MODEL.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

print("✅ Environment metrics corrigées en dictionnaire")
