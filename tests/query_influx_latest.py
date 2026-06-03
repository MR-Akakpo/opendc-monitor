from influxdb_client import InfluxDBClient

URL = "http://localhost:8086"
TOKEN = "stellarix-token"
ORG = "stellarix"
BUCKET = "datacenter"

query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -15m)
  |> limit(n: 20)
'''

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
tables = client.query_api().query(query)

count = 0
for table in tables:
    for record in table.records:
        count += 1
        print(record.get_measurement(), record.values.get("equipment"), record.values.get("metric"), record.get_field(), record.get_value())

print("TOTAL:", count)
client.close()
