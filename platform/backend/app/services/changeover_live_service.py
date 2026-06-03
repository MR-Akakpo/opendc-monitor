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
    default = {
        "lead_generator": "GENERATOR_A",
        "lag_generator": "GENERATOR_B",
        "transfer_time_seconds": 5
    }

    try:
        if CONTROL_FILE.exists():
            data = json.loads(CONTROL_FILE.read_text(encoding="utf-8"))
            lead = str(data.get("lead_generator", "GENERATOR_A")).upper()
            if lead not in ["GENERATOR_A", "GENERATOR_B"]:
                lead = "GENERATOR_A"
            lag = "GENERATOR_B" if lead == "GENERATOR_A" else "GENERATOR_A"

            return {
                "lead_generator": lead,
                "lag_generator": lag,
                "transfer_time_seconds": int(data.get("transfer_time_seconds", 5))
            }
    except Exception:
        pass

    return default


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


def get_changeover_live_data():
    control = read_control()
    lead = control["lead_generator"]
    lag = control["lag_generator"]
    transfer_time = control["transfer_time_seconds"]

    gen_a_priority = "LEAD" if lead == "GENERATOR_A" else "LAG"
    gen_b_priority = "LEAD" if lead == "GENERATOR_B" else "LAG"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "INFLUXDB",
        "utility": {
            "voltage": num("UTILITY", "voltage"),
            "frequency": num("UTILITY", "frequency"),
            "status": state("UTILITY", "status") or "ACTIVE",
            "available": state("UTILITY", "available") or "TRUE",
            "priority": state("UTILITY", "priority") or "PRIORITY_1"
        },
        "generator_a": {
            "voltage": num("GENERATOR_A", "voltage"),
            "frequency": num("GENERATOR_A", "frequency"),
            "status": state("GENERATOR_A", "status") or "AVAILABLE",
            "available": state("GENERATOR_A", "available") or "TRUE",
            "running": state("GENERATOR_A", "running") or "FALSE",
            "on_load": state("GENERATOR_A", "on_load") or "FALSE",
            "priority": gen_a_priority,
            "priority_rank": 2 if gen_a_priority == "LEAD" else 3
        },
        "generator_b": {
            "voltage": num("GENERATOR_B", "voltage"),
            "frequency": num("GENERATOR_B", "frequency"),
            "status": state("GENERATOR_B", "status") or "AVAILABLE",
            "available": state("GENERATOR_B", "available") or "TRUE",
            "running": state("GENERATOR_B", "running") or "FALSE",
            "on_load": state("GENERATOR_B", "on_load") or "FALSE",
            "priority": gen_b_priority,
            "priority_rank": 2 if gen_b_priority == "LEAD" else 3
        },
        "tco_a": {
            "status": state("TCO_A", "status") or "NORMAL",
            "selected_source": state("TCO_A", "selected_source") or "UTILITY",
            "mode": state("TCO_A", "mode") or "AUTO",
            "lead_lag": f"{lead}=LEAD",
            "state": state("TCO_A", "state") or "READY",
            "position": state("TCO_A", "position") or "UTILITY",
            "input_1": state("TCO_A", "input_1") or "UTILITY",
            "input_2": lead
        },
        "tco_b": {
            "status": state("TCO_B", "status") or "NORMAL",
            "selected_source": state("TCO_B", "selected_source") or "TCO_A_OUTPUT",
            "mode": state("TCO_B", "mode") or "AUTO",
            "lead_lag": f"{lag}=LAG",
            "state": state("TCO_B", "state") or "READY",
            "position": state("TCO_B", "position") or "TCO_A_OUTPUT",
            "input_1": state("TCO_B", "input_1") or "TCO_A_OUTPUT",
            "input_2": lag
        },
        "ats": {
            "status": state("ATS", "status") or "NORMAL",
            "selected_source": state("ATS", "selected_source") or "UTILITY",
            "mode": state("ATS", "mode") or "AUTO",
            "transfer_count": num("ATS", "transfer_count") or 0,
            "transfer_duration": transfer_time,
            "last_transfer": state("ATS", "last_transfer") or "NO_RECENT_TRANSFER",
            "transfer_state": state("ATS", "transfer_state") or "IDLE",
            "site_supply": state("ATS", "site_supply") or "SENELEC",
            "lead_generator": lead,
            "lag_generator": lag
        },
        "control": control
    }

