import json
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parents[3]

def read_yaml(relative_path):
    path = BASE_DIR / relative_path
    if not path.exists():
        return {'error': f'{relative_path} not found'}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def read_json(relative_path):
    path = BASE_DIR / relative_path
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_jsonl(relative_path, limit=100):
    path = BASE_DIR / relative_path
    if not path.exists():
        return []
    lines = path.read_text(encoding='utf-8').splitlines()
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    return events
