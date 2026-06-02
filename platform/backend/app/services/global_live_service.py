from datetime import datetime, timezone
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "stellarix-token"
INFLUX_ORG = "stellarix"
INFLUX_BUCKET = "datacenter"


def latest_value(equipment: str, metric: str, field: str = "value"):
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30m)
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


def numeric(equipment: str, metric: str):
    value = latest_value(equipment, metric, "value")
    try:
        return round(float(value), 2)
    except Exception:
        return None


def state(equipment: str, metric: str):
    value = latest_value(equipment, metric, "state_value")
    if value is None:
        return None
    return str(value)


def get_global_live_data():
    utility_voltage = numeric("UTILITY_INPUT", "voltage")
    utility_frequency = numeric("UTILITY_INPUT", "frequency")

    pdu_a_power = numeric("PDU_IT_A", "power") or 0
    pdu_b_power = numeric("PDU_IT_B", "power") or 0
    total_it_load = round(pdu_a_power + pdu_b_power, 2)

    mps_power = numeric("MPS_OUTPUT", "power") or 0
    pue = round(mps_power / total_it_load, 2) if total_it_load > 0 else None

    battery_soc_a = numeric("BATTERY_BANK_A", "soc")
    battery_soc_b = numeric("BATTERY_BANK_B", "soc")

    ats_source = state("ATS", "selected_source")
    ats_status = state("ATS", "status")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "INFLUXDB",
        "utility": {
            "voltage": utility_voltage,
            "frequency": utility_frequency,
            "status": state("UTILITY_INPUT", "status") or "ACTIVE"
        },
        "ats": {
            "selected_source": ats_source,
            "status": ats_status
        },
        "ups_a": {
            "load": numeric("UPS_A", "load"),
            "output_voltage": numeric("UPS_A", "output_voltage"),
            "status": state("UPS_A", "status")
        },
        "ups_b": {
            "load": numeric("UPS_B", "load"),
            "output_voltage": numeric("UPS_B", "output_voltage"),
            "status": state("UPS_B", "status")
        },
        "battery_bank_a": {
            "soc": battery_soc_a,
            "status": state("BATTERY_BANK_A", "status")
        },
        "battery_bank_b": {
            "soc": battery_soc_b,
            "status": state("BATTERY_BANK_B", "status")
        },
        "it": {
            "total_load_kw": total_it_load if total_it_load > 0 else None,
            "pue": pue,
            "status": "NORMAL"
        },
        "site": {
            "status": "NORMAL"
        }
    }
