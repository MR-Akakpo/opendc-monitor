from datetime import datetime, timezone
from pathlib import Path
import yaml
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "stellarix-token"
INFLUX_ORG = "stellarix"
INFLUX_BUCKET = "datacenter"

def sensor_status(temp, humidity):
    if temp is None or humidity is None:
        return "NO DATA"
    if temp >= 30 or humidity >= 70 or humidity <= 25:
        return "CRITICAL"
    if temp >= 27 or humidity >= 60 or humidity <= 30:
        return "WARNING"
    return "NORMAL"

def load_expected_sensors():
    model_path = Path(__file__).resolve().parents[3] / "configs" / "datacenter_model.yaml"
    data = yaml.safe_load(model_path.read_text(encoding="utf-8"))
    zones = data["systems"]["environment"]["zones"]

    sensors = {}
    for zone_key, zone in zones.items():
        for sensor in zone["sensors"]:
            equipment_id = f"{zone_key}_{sensor}".upper()
            sensors[equipment_id] = {
                "zone": zone_key,
                "zone_label": zone["label"],
                "equipment": sensor,
                "equipment_id": equipment_id,
                "temperature": None,
                "humidity": None,
                "last_update": None,
                "status": "NO DATA"
            }
    return sensors

def latest_environment_records():
    sensors = load_expected_sensors()

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30m)
      |> filter(fn: (r) => r["_measurement"] == "environment")
      |> last()
    '''

    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            tables = client.query_api().query(query)

            for table in tables:
                for record in table.records:
                    equipment = str(record.values.get("equipment", "")).upper()
                    metric = record.values.get("metric", "")
                    value = record.get_value()
                    record_time = record.get_time().isoformat()

                    if equipment in sensors and record.get_field() == "value":
                        if metric == "temperature":
                            sensors[equipment]["temperature"] = round(float(value), 2)
                        if metric == "humidity":
                            sensors[equipment]["humidity"] = round(float(value), 2)

                        sensors[equipment]["last_update"] = record_time
    except Exception:
        pass

    result = []
    for sensor in sensors.values():
        sensor["status"] = sensor_status(sensor["temperature"], sensor["humidity"])
        result.append(sensor)

    return result

def get_environment_live_data():
    sensors = latest_environment_records()

    normal = len([s for s in sensors if s["status"] == "NORMAL"])
    warning = len([s for s in sensors if s["status"] == "WARNING"])
    critical = len([s for s in sensors if s["status"] == "CRITICAL"])
    nodata = len([s for s in sensors if s["status"] == "NO DATA"])

    temps = [s["temperature"] for s in sensors if s["temperature"] is not None]
    hums = [s["humidity"] for s in sensors if s["humidity"] is not None]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "INFLUXDB",
        "status": "NORMAL" if critical == 0 and warning == 0 else "WARNING" if critical == 0 else "CRITICAL",
        "summary": {
            "total_sensors": len(sensors),
            "normal": normal,
            "warning": warning,
            "critical": critical,
            "no_data": nodata,
            "avg_temperature": round(sum(temps) / len(temps), 2) if temps else None,
            "avg_humidity": round(sum(hums) / len(hums), 2) if hums else None
        },
        "sensors": sensors
    }
