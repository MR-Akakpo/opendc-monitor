from datetime import datetime, timezone
from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "stellarix-token"
INFLUX_ORG = "stellarix"
INFLUX_BUCKET = "datacenter"

PERIODS = {
    "1h": "-1h",
    "6h": "-6h",
    "12h": "-12h",
    "24h": "-24h",
    "7d": "-7d",
    "30d": "-30d",
}

def get_history_data(system: str, equipment: str, metric: str, period: str = "24h"):
    range_value = PERIODS.get(period, "-24h")

    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: {range_value})
      |> filter(fn: (r) => r["_measurement"] == "{system}")
      |> filter(fn: (r) => r["equipment"] == "{equipment}")
      |> filter(fn: (r) => r["metric"] == "{metric}")
      |> filter(fn: (r) => r["_field"] == "value")
      |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
      |> yield(name: "mean")
    '''

    points = []

    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            tables = client.query_api().query(query)

            for table in tables:
                for record in table.records:
                    points.append({
                        "timestamp": record.get_time().isoformat(),
                        "value": round(float(record.get_value()), 3)
                    })

    except Exception as e:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "ERROR",
            "error": str(e),
            "system": system,
            "equipment": equipment,
            "metric": metric,
            "period": period,
            "points": []
        }

    values = [p["value"] for p in points]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "OK",
        "system": system,
        "equipment": equipment,
        "metric": metric,
        "period": period,
        "count": len(points),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "avg": round(sum(values) / len(values), 3) if values else None,
        "points": points
    }
