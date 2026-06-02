import json
from pathlib import Path
from collections import Counter

EVENTS_FILE = Path("monitoring/events/events.jsonl")
OUTPUT_FILE = Path("monitoring/historian/daily_statistics.json")

stats = {
    "total_events": 0,
    "alarms_raised": 0,
    "alarms_cleared": 0,
    "critical_events": 0,
    "warning_events": 0,
    "top_equipment": {}
}

equipment_counter = Counter()

if EVENTS_FILE.exists():

    with open(EVENTS_FILE, "r", encoding="utf-8") as f:

        for line in f:

            try:
                event = json.loads(line)

                stats["total_events"] += 1

                equipment = event.get("equipment")
                severity = event.get("severity")

                if equipment:
                    equipment_counter[equipment] += 1

                if event.get("event_type") == "ALARM_RAISED":
                    stats["alarms_raised"] += 1

                if event.get("event_type") == "ALARM_CLEARED":
                    stats["alarms_cleared"] += 1

                if severity == "CRITICAL":
                    stats["critical_events"] += 1

                if severity == "WARNING":
                    stats["warning_events"] += 1

            except Exception:
                pass

stats["top_equipment"] = dict(
    equipment_counter.most_common(20)
)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(stats, f, indent=2)

print("✅ Statistics generated")
print(json.dumps(stats, indent=2))
