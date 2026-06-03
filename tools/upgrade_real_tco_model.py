import yaml
import subprocess
from pathlib import Path
from datetime import datetime
import shutil

MODEL = Path("configs/datacenter_model.yaml")
BACKUP = Path("configs/backups") / f"datacenter_model_before_real_tco_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
BACKUP.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(MODEL, BACKUP)

model = yaml.safe_load(MODEL.read_text(encoding="utf-8"))
eq = model["systems"]["changeover"]["equipments"]

for gen in ["generator_a", "generator_b"]:
    eq[gen]["metrics"].update({
        "priority_rank": f"CHANGEOVER/{gen.upper()}/priority_rank"
    })

eq["tco_a"]["label"] = "TCO A - Triple Change Over TGBT A"
eq["tco_a"]["metrics"].update({
    "output": "CHANGEOVER/TCO_A/output",
    "source_1": "CHANGEOVER/TCO_A/source_1",
    "source_2": "CHANGEOVER/TCO_A/source_2",
    "source_3": "CHANGEOVER/TCO_A/source_3",
    "default_primary_backup": "CHANGEOVER/TCO_A/default_primary_backup",
    "default_secondary_backup": "CHANGEOVER/TCO_A/default_secondary_backup",
    "effective_primary_backup": "CHANGEOVER/TCO_A/effective_primary_backup",
    "effective_secondary_backup": "CHANGEOVER/TCO_A/effective_secondary_backup",
    "synchronized_with": "CHANGEOVER/TCO_A/synchronized_with"
})

eq["tco_b"]["label"] = "TCO B - Triple Change Over TGBT B"
eq["tco_b"]["metrics"].update({
    "output": "CHANGEOVER/TCO_B/output",
    "source_1": "CHANGEOVER/TCO_B/source_1",
    "source_2": "CHANGEOVER/TCO_B/source_2",
    "source_3": "CHANGEOVER/TCO_B/source_3",
    "default_primary_backup": "CHANGEOVER/TCO_B/default_primary_backup",
    "default_secondary_backup": "CHANGEOVER/TCO_B/default_secondary_backup",
    "effective_primary_backup": "CHANGEOVER/TCO_B/effective_primary_backup",
    "effective_secondary_backup": "CHANGEOVER/TCO_B/effective_secondary_backup",
    "synchronized_with": "CHANGEOVER/TCO_B/synchronized_with"
})

MODEL.write_text(yaml.dump(model, sort_keys=False, allow_unicode=True), encoding="utf-8")

print(f"✅ Backup: {BACKUP}")
print("✅ Real TCO model upgraded")

subprocess.run(["python", "deployment/scripts/generate_mqtt_topics.py"], check=True)
