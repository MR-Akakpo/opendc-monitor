import yaml
from pathlib import Path

MODEL = Path("configs/datacenter_model.yaml")
data = yaml.safe_load(MODEL.read_text(encoding="utf-8"))

env = data["systems"]["environment"]

env["metrics"] = {
    "temperature": {
        "unit": "°C",
        "type": "numeric",
        "topic_template": "stellarix/stellarix_dc01/environment/{room}/temperature"
    },
    "humidity": {
        "unit": "%",
        "type": "numeric",
        "topic_template": "stellarix/stellarix_dc01/environment/{room}/humidity"
    }
}

MODEL.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

print("✅ Environment metrics corrigées avec topic_template")
