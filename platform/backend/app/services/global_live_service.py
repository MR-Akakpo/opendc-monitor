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
    try:
        value = latest_value(equipment, metric, "value")
        return round(float(value), 2)
    except Exception:
        return None

def state(equipment: str, metric: str):
    value = latest_value(equipment, metric, "state_value")
    return str(value) if value is not None else None

def status_from_voltage(v):
    if v is None:
        return "UNKNOWN"
    if v >= 350:
        return "AVAILABLE"
    if v > 50:
        return "WARNING"
    return "UNAVAILABLE"

def get_global_live_data():
    utility_voltage = numeric("UTILITY_INPUT", "voltage") or numeric("TCO_A_UTILITY", "voltage")
    utility_frequency = numeric("UTILITY_INPUT", "frequency") or numeric("TCO_A_UTILITY", "frequency")

    ats_source = state("ATS", "selected_source") or "UNKNOWN"
    ats_mode = state("ATS", "mode") or "UNKNOWN"
    ats_status = state("ATS", "status") or "UNKNOWN"

    gen_a_voltage = numeric("TCO_A_GENERATOR_A", "voltage") or numeric("TCO_B_GENERATOR_A", "voltage")
    gen_b_voltage = numeric("TCO_A_GENERATOR_B", "voltage") or numeric("TCO_B_GENERATOR_B", "voltage")

    gen_a_status = "ON LOAD" if ats_source == "GENERATOR_A" else status_from_voltage(gen_a_voltage)
    gen_b_status = "ON LOAD" if ats_source == "GENERATOR_B" else status_from_voltage(gen_b_voltage)

    pdu_a_power = numeric("PDU_IT_A", "power") or 0
    pdu_b_power = numeric("PDU_IT_B", "power") or 0
    total_it_load = round(pdu_a_power + pdu_b_power, 2)

    mps_power = numeric("MPS_OUTPUT", "power") or 0
    pue = round(mps_power / total_it_load, 2) if total_it_load > 0 else None

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "INFLUXDB",
        "utility": {
            "voltage": utility_voltage,
            "frequency": utility_frequency,
            "status": "ACTIVE" if utility_voltage and utility_voltage >= 350 else "UNAVAILABLE"
        },
        "generator_a": {
            "voltage": gen_a_voltage,
            "status": gen_a_status
        },
        "generator_b": {
            "voltage": gen_b_voltage,
            "status": gen_b_status
        },
        "ats": {
            "selected_source": ats_source,
            "mode": ats_mode,
            "status": ats_status
        },
        "sps_a": {
            "voltage": numeric("SPS_A", "voltage"),
            "load": numeric("SPS_A", "load_percent"),
            "status": "NORMAL"
        },
        "sps_b": {
            "voltage": numeric("SPS_B", "voltage"),
            "load": numeric("SPS_B", "load_percent"),
            "status": "NORMAL"
        },
        "ups_a": {
            "load": numeric("UPS_A", "load"),
            "output_voltage": numeric("UPS_A", "output_voltage"),
            "status": state("UPS_A", "status") or "NORMAL"
        },
        "ups_b": {
            "load": numeric("UPS_B", "load"),
            "output_voltage": numeric("UPS_B", "output_voltage"),
            "status": state("UPS_B", "status") or "NORMAL"
        },
        "rectifier_a": {
            "voltage": numeric("RECTIFIER_A", "dc_voltage"),
            "current": numeric("RECTIFIER_A", "current"),
            "status": state("RECTIFIER_A", "status") or "NORMAL"
        },
        "rectifier_b": {
            "voltage": numeric("RECTIFIER_B", "dc_voltage"),
            "current": numeric("RECTIFIER_B", "current"),
            "status": state("RECTIFIER_B", "status") or "NORMAL"
        },
        "battery_bank_a": {
            "soc": numeric("BATTERY_BANK_A", "soc"),
            "status": state("BATTERY_BANK_A", "status") or "HEALTHY"
        },
        "battery_bank_b": {
            "soc": numeric("BATTERY_BANK_B", "soc"),
            "status": state("BATTERY_BANK_B", "status") or "HEALTHY"
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
