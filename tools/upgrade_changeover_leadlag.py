import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import yaml

MODEL = Path("configs/datacenter_model.yaml")
BACKUP_DIR = Path("configs/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

backup = BACKUP_DIR / f"datacenter_model_before_leadlag_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
shutil.copy2(MODEL, backup)

model = yaml.safe_load(MODEL.read_text(encoding="utf-8"))
equipments = model["systems"]["changeover"]["equipments"]

equipments["utility"]["metrics"].update({
    "available": "CHANGEOVER/UTILITY/available",
    "priority": "CHANGEOVER/UTILITY/priority"
})

equipments["generator_a"]["metrics"].update({
    "running": "CHANGEOVER/GENERATOR_A/running",
    "priority": "CHANGEOVER/GENERATOR_A/priority"
})

equipments["generator_b"]["metrics"].update({
    "running": "CHANGEOVER/GENERATOR_B/running",
    "priority": "CHANGEOVER/GENERATOR_B/priority"
})

equipments["tco_a"]["metrics"].update({
    "position": "CHANGEOVER/TCO_A/position",
    "input_1": "CHANGEOVER/TCO_A/input_1",
    "input_2": "CHANGEOVER/TCO_A/input_2"
})

equipments["tco_b"]["metrics"].update({
    "position": "CHANGEOVER/TCO_B/position",
    "input_1": "CHANGEOVER/TCO_B/input_1",
    "input_2": "CHANGEOVER/TCO_B/input_2"
})

equipments["ats"]["metrics"].update({
    "site_supply": "CHANGEOVER/ATS/site_supply",
    "lead_generator": "CHANGEOVER/ATS/lead_generator",
    "lag_generator": "CHANGEOVER/ATS/lag_generator"
})

MODEL.write_text(yaml.dump(model, sort_keys=False, allow_unicode=True), encoding="utf-8")

print(f"✅ Backup créé: {backup}")
print("✅ Modèle Change Over corrigé : SENELEC prioritaire + Lead/Lag + TCO positions")

subprocess.run(["python", "deployment/scripts/generate_mqtt_topics.py"], check=True)
