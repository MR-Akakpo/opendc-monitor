from datetime import datetime, timezone
from pathlib import Path
import json
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "stellarix-token"
INFLUX_ORG = "stellarix"
INFLUX_BUCKET = "datacenter"
CONTROL_FILE = Path("runtime/changeover_control.json")

def read_control():
    try:
        data = json.loads(CONTROL_FILE.read_text(encoding="utf-8"))
        lead = str(data.get("lead_generator", "GENERATOR_A")).upper()
        if lead not in ["GENERATOR_A", "GENERATOR_B"]:
            lead = "GENERATOR_A"
        lag = "GENERATOR_B" if lead == "GENERATOR_A" else "GENERATOR_A"
        return {"lead_generator": lead, "lag_generator": lag, "transfer_time_seconds": int(data.get("transfer_time_seconds", 5))}
    except Exception:
        return {"lead_generator": "GENERATOR_A", "lag_generator": "GENERATOR_B", "transfer_time_seconds": 5}

def latest(equipment: str, metric: str, field: str):
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30m)
      |> filter(fn: (r) => r["_measurement"] == "changeover")
      |> filter(fn: (r) => r["equipment"] == "{equipment}")
      |> filter(fn: (r) => r["metric"] == "{metric}")
      |> filter(fn: (r) => r["_field"] == "{field}")
      |> last()
    '''
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            tables = client.query_api().query(query)
            for table in tables:
                for record in table.records:
                    return record.get_value()
    except Exception:
        return None
    return None

def num(equipment, metric):
    try:
        v = latest(equipment, metric, "value")
        return round(float(v), 2)
    except Exception:
        return None

def state(equipment, metric):
    v = latest(equipment, metric, "state_value")
    return str(v) if v is not None else None

def gen_payload(name, control):
    priority = "LEAD" if control["lead_generator"] == name else "LAG"
    return {
        "voltage": num(name, "voltage"),
        "frequency": num(name, "frequency"),
        "status": state(name, "status") or "AVAILABLE",
        "available": state(name, "available") or "TRUE",
        "running": state(name, "running") or "FALSE",
        "on_load": state(name, "on_load") or "FALSE",
        "priority": priority,
        "priority_rank": 2 if priority == "LEAD" else 3,
    }

def tco_payload(name, output, default_primary, default_secondary, sync, control):
    return {
        "status": state(name, "status") or "NORMAL",
        "selected_source": state(name, "selected_source") or "UTILITY",
        "mode": state(name, "mode") or "AUTO",
        "lead_lag": f"{control['lead_generator']}=LEAD",
        "state": state(name, "state") or "READY",
        "position": state(name, "position") or "UTILITY",
        "source_1": state(name, "source_1") or "UTILITY",
        "source_2": state(name, "source_2") or "GENERATOR_A",
        "source_3": state(name, "source_3") or "GENERATOR_B",
        "output": state(name, "output") or output,
        "default_primary_backup": state(name, "default_primary_backup") or default_primary,
        "default_secondary_backup": state(name, "default_secondary_backup") or default_secondary,
        "effective_primary_backup": control["lead_generator"],
        "effective_secondary_backup": control["lag_generator"],
        "synchronized_with": state(name, "synchronized_with") or sync,
    }

def get_changeover_live_data():
    control = read_control()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "INFLUXDB",
        "utility": {
            "voltage": num("UTILITY", "voltage"),
            "frequency": num("UTILITY", "frequency"),
            "status": state("UTILITY", "status") or "ACTIVE",
            "available": state("UTILITY", "available") or "TRUE",
            "priority": state("UTILITY", "priority") or "PRIORITY_1",
            "priority_rank": 1,
        },
        "generator_a": gen_payload("GENERATOR_A", control),
        "generator_b": gen_payload("GENERATOR_B", control),
        "tco_a": tco_payload("TCO_A", "TGBT_A", "GENERATOR_A", "GENERATOR_B", "TCO_B", control),
        "tco_b": tco_payload("TCO_B", "TGBT_B", "GENERATOR_B", "GENERATOR_A", "TCO_A", control),
        "ats": {
            "status": state("ATS", "status") or "NORMAL",
            "selected_source": state("ATS", "selected_source") or "UTILITY",
            "mode": state("ATS", "mode") or "AUTO",
            "transfer_count": num("ATS", "transfer_count") or 0,
            "transfer_duration": control["transfer_time_seconds"],
            "last_transfer": state("ATS", "last_transfer") or "NO_RECENT_TRANSFER",
            "transfer_state": state("ATS", "transfer_state") or "IDLE",
            "site_supply": state("ATS", "site_supply") or "SENELEC",
            "lead_generator": control["lead_generator"],
            "lag_generator": control["lag_generator"],
        },
        "control": control,
    }
