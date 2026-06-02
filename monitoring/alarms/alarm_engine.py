import json
import yaml
from pathlib import Path
from datetime import datetime, timezone

THRESHOLDS_FILE = Path("configs/thresholds.yaml")
ACTIVE_ALARMS_FILE = Path("monitoring/alarms/active_alarms.json")
EVENTS_FILE = Path("monitoring/events/events.jsonl")

def load_thresholds():
    with open(THRESHOLDS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("thresholds", {})

def classify_status(system, metric, value):
    thresholds = load_thresholds()

    if system not in thresholds:
        return "UNKNOWN"

    if metric not in thresholds[system]:
        return "UNKNOWN"

    rule = thresholds[system][metric]

    if not isinstance(value, (int, float)):
        return "UNKNOWN"

    critical_min = rule.get("critical_min")
    critical_max = rule.get("critical_max")
    warning_min = rule.get("warning_min")
    warning_max = rule.get("warning_max")
    normal_min = rule.get("normal_min")
    normal_max = rule.get("normal_max")

    if critical_min is not None and value < critical_min:
        return "CRITICAL"

    if critical_max is not None and value > critical_max:
        return "CRITICAL"

    if warning_min is not None and value < warning_min:
        return "WARNING"

    if warning_max is not None and value > warning_max:
        return "WARNING"

    if normal_min is not None and value < normal_min:
        return "WARNING"

    if normal_max is not None and value > normal_max:
        return "WARNING"

    return "NORMAL"

def load_active_alarms():
    if not ACTIVE_ALARMS_FILE.exists():
        return {}

    try:
        with open(ACTIVE_ALARMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_active_alarms(active_alarms):
    with open(ACTIVE_ALARMS_FILE, "w", encoding="utf-8") as f:
        json.dump(active_alarms, f, indent=2)

def write_event(event):
    with open(EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

def process_alarm(payload, status):
    active_alarms = load_active_alarms()

    alarm_key = f"{payload.get('site')}|{payload.get('system')}|{payload.get('equipment')}|{payload.get('metric')}"

    now = datetime.now(timezone.utc).isoformat()

    current_alarm = active_alarms.get(alarm_key)

    if status in ["WARNING", "CRITICAL"]:
        if current_alarm is None:
            event = {
                "event_type": "ALARM_RAISED",
                "severity": status,
                "site": payload.get("site"),
                "system": payload.get("system"),
                "zone": payload.get("zone"),
                "equipment": payload.get("equipment"),
                "metric": payload.get("metric"),
                "value": payload.get("value"),
                "timestamp": now
            }

            active_alarms[alarm_key] = event
            write_event(event)

            print(f"🚨 ALARM RAISED | {status} | {payload.get('equipment')} | {payload.get('metric')} = {payload.get('value')}")

        elif current_alarm.get("severity") != status:
            event = {
                "event_type": "ALARM_SEVERITY_CHANGED",
                "old_severity": current_alarm.get("severity"),
                "new_severity": status,
                "site": payload.get("site"),
                "system": payload.get("system"),
                "zone": payload.get("zone"),
                "equipment": payload.get("equipment"),
                "metric": payload.get("metric"),
                "value": payload.get("value"),
                "timestamp": now
            }

            active_alarms[alarm_key] = event
            write_event(event)

            print(f"⚠️ ALARM UPDATED | {payload.get('equipment')} | {payload.get('metric')} | {status}")

    elif status == "NORMAL":
        if current_alarm is not None:
            event = {
                "event_type": "ALARM_CLEARED",
                "old_severity": current_alarm.get("severity"),
                "severity": "NORMAL",
                "site": payload.get("site"),
                "system": payload.get("system"),
                "zone": payload.get("zone"),
                "equipment": payload.get("equipment"),
                "metric": payload.get("metric"),
                "value": payload.get("value"),
                "timestamp": now
            }

            active_alarms.pop(alarm_key, None)
            write_event(event)

            print(f"✅ ALARM CLEARED | {payload.get('equipment')} | {payload.get('metric')}")

    save_active_alarms(active_alarms)

    return active_alarms
