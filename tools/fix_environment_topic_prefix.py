import yaml
from pathlib import Path

MODEL = Path("configs/datacenter_model.yaml")
data = yaml.safe_load(MODEL.read_text(encoding="utf-8"))

env = data["systems"]["environment"]

env["metrics"]["temperature"]["topic_template"] = "environment/{room}/temperature"
env["metrics"]["humidity"]["topic_template"] = "environment/{room}/humidity"

MODEL.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")

print("✅ topic_template Environment corrigé sans préfixe doublé")
