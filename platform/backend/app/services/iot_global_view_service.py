import os
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient

load_dotenv()

INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "stellarix-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "stellarix")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "datacenter")


def read_latest_iot_values():
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -15m)
      |> last()
    '''

    result = {}

    try:
        with InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        ) as client:
            tables = client.query_api().query(query)

            for table in tables:
                for record in table.records:
                    topic = (
                        record.values.get("topic")
                        or record.values.get("mqtt_topic")
                        or record.values.get("equipment")
                        or record.get_measurement()
                    )

                    field = record.get_field()
                    value = record.get_value()

                    key = f"{topic}/{field}".lower()
                    result[key] = value

    except Exception as e:
        return {
            "source": "INFLUXDB",
            "status": "ERROR",
            "error": str(e),
            "values": {}
        }

    return {
        "source": "INFLUXDB",
        "status": "OK" if result else "NO_DATA",
        "values": result
    }


def find_value(values, keywords, default=None):
    for key, value in values.items():
        if all(k.lower() in key.lower() for k in keywords):
            return value
    return default


def build_global_view_payload():
    raw = read_latest_iot_values()
    values = raw.get("values", {})

    return {
        "source": raw["source"],
        "data_status": raw["status"],
        "utility": {
            "voltage": find_value(values, ["utility", "voltage"]),
            "frequency": find_value(values, ["utility", "frequency"]),
            "status": find_value(values, ["utility", "status"], "UNKNOWN")
        },
        "generator_a": {
            "status": find_value(values, ["generator_a", "status"], "UNKNOWN"),
            "power": find_value(values, ["generator_a", "power"])
        },
        "generator_b": {
            "status": find_value(values, ["generator_b", "status"], "UNKNOWN"),
            "power": find_value(values, ["generator_b", "power"])
        },
        "ats": {
            "selected_source": find_value(values, ["ats", "source"], "UNKNOWN"),
            "status": find_value(values, ["ats", "status"], "UNKNOWN")
        },
        "sps_a": {
            "voltage": find_value(values, ["sps_a", "voltage"]),
            "load": find_value(values, ["sps_a", "load"]),
            "status": find_value(values, ["sps_a", "status"], "UNKNOWN")
        },
        "sps_b": {
            "voltage": find_value(values, ["sps_b", "voltage"]),
            "load": find_value(values, ["sps_b", "load"]),
            "status": find_value(values, ["sps_b", "status"], "UNKNOWN")
        },
        "ups_a": {
            "load": find_value(values, ["ups_a", "load"]),
            "output_voltage": find_value(values, ["ups_a", "voltage"]),
            "status": find_value(values, ["ups_a", "status"], "UNKNOWN")
        },
        "ups_b": {
            "load": find_value(values, ["ups_b", "load"]),
            "output_voltage": find_value(values, ["ups_b", "voltage"]),
            "status": find_value(values, ["ups_b", "status"], "UNKNOWN")
        },
        "rectifier_a": {
            "current": find_value(values, ["rectifier_a", "current"]),
            "voltage": find_value(values, ["rectifier_a", "voltage"]),
            "status": find_value(values, ["rectifier_a", "status"], "UNKNOWN")
        },
        "rectifier_b": {
            "current": find_value(values, ["rectifier_b", "current"]),
            "voltage": find_value(values, ["rectifier_b", "voltage"]),
            "status": find_value(values, ["rectifier_b", "status"], "UNKNOWN")
        },
        "battery_bank_a": {
            "soc": find_value(values, ["battery_bank_a", "soc"]),
            "status": find_value(values, ["battery_bank_a", "status"], "UNKNOWN")
        },
        "battery_bank_b": {
            "soc": find_value(values, ["battery_bank_b", "soc"]),
            "status": find_value(values, ["battery_bank_b", "status"], "UNKNOWN")
        },
        "it": {
            "total_load_kw": find_value(values, ["it", "load"]),
            "pue": find_value(values, ["pue"]),
            "status": find_value(values, ["it", "status"], "UNKNOWN")
        }
    }
