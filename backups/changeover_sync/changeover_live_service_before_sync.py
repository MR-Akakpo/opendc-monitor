from datetime import datetime, timezone
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "stellarix-token"
INFLUX_ORG = "stellarix"
INFLUX_BUCKET = "datacenter"

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
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "INFLUXDB",
        "utility": {
            "voltage": num("UTILITY", "voltage"),
            "frequency": num("UTILITY", "frequency"),
            "status": state("UTILITY", "status"),
            "available": state("UTILITY", "available"),
            "priority": state("UTILITY", "priority")
        },
        "generator_a": {
            "voltage": num("GENERATOR_A", "voltage"),
            "frequency": num("GENERATOR_A", "frequency"),
            "status": state("GENERATOR_A", "status"),
            "available": state("GENERATOR_A", "available"),
            "running": state("GENERATOR_A", "running"),
            "on_load": state("GENERATOR_A", "on_load"),
            "priority": state("GENERATOR_A", "priority")
        },
        "generator_b": {
            "voltage": num("GENERATOR_B", "voltage"),
            "frequency": num("GENERATOR_B", "frequency"),
            "status": state("GENERATOR_B", "status"),
            "available": state("GENERATOR_B", "available"),
            "running": state("GENERATOR_B", "running"),
            "on_load": state("GENERATOR_B", "on_load"),
            "priority": state("GENERATOR_B", "priority")
        },
        "tco_a": {
            "status": state("TCO_A", "status"),
            "selected_source": state("TCO_A", "selected_source"),
            "mode": state("TCO_A", "mode"),
            "lead_lag": state("TCO_A", "lead_lag"),
            "state": state("TCO_A", "state"),
            "position": state("TCO_A", "position"),
            "input_1": state("TCO_A", "input_1"),
            "input_2": state("TCO_A", "input_2")
        },
        "tco_b": {
            "status": state("TCO_B", "status"),
            "selected_source": state("TCO_B", "selected_source"),
            "mode": state("TCO_B", "mode"),
            "lead_lag": state("TCO_B", "lead_lag"),
            "state": state("TCO_B", "state"),
            "position": state("TCO_B", "position"),
            "input_1": state("TCO_B", "input_1"),
            "input_2": state("TCO_B", "input_2")
        },
        "ats": {
            "status": state("ATS", "status"),
            "selected_source": state("ATS", "selected_source"),
            "mode": state("ATS", "mode"),
            "transfer_count": num("ATS", "transfer_count"),
            "transfer_duration": num("ATS", "transfer_duration"),
            "last_transfer": state("ATS", "last_transfer"),
            "transfer_state": state("ATS", "transfer_state"),
            "site_supply": state("ATS", "site_supply"),
            "lead_generator": state("ATS", "lead_generator"),
            "lag_generator": state("ATS", "lag_generator")
        }
    }
