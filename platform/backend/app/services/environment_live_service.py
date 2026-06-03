from datetime import datetime, timezone
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "stellarix-token"
INFLUX_ORG = "stellarix"
INFLUX_BUCKET = "datacenter"

def latest_environment_records():
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30m)
      |> filter(fn: (r) => r["_measurement"] == "environment")
      |> last()
    '''

    sensors = {}

    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            tables = client.query_api().query(query)

            for table in tables:
                for record in table.records:
                    zone = record.values.get("zone", "unknown")
                    equipment = record.values.get("equipment", "unknown")
                    metric = record.values.get("metric", "unknown")
                    field = record.get_field()
                    value = record.get_value()

                    key = f"{zone}:{equipment}"

                    if key not in sensors:
                        sensors[key] = {
                            "zone": zone,
                            "equipment": equipment,
                            "temperature": None,
                            "humidity": None,
                            "status": "NO DATA"
                        }

                    if field == "value":
                        if metric == "temperature":
                            sensors[key]["temperature"] = round(float(value), 2)
                        if metric == "humidity":
                            sensors[key]["humidity"] = round(float(value), 2)

        return list(sensors.values())

    except Exception:
        return []

def sensor_status(temp, humidity):
    if temp is None or humidity is None:
        return "NO DATA"

    if temp >= 30 or humidity >= 70 or humidity <= 25:
        return "CRITICAL"

    if temp >= 27 or humidity >= 60 or humidity <= 30:
        return "WARNING"

    return "NORMAL"

def group_zone(zone):
    z = str(zone).lower()

    if "battery" in z:
        return "Battery Room"
    if "energy" in z:
        return "Energy Centre"
    if "it" in z:
        return "IT Room"
    if "transmission" in z:
        return "Transmission Room"

    return "Other"

def get_environment_live_data():
    sensors = latest_environment_records()

    for s in sensors:
        s["zone_label"] = group_zone(s["zone"])
        s["status"] = sensor_status(s["temperature"], s["humidity"])

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
