from kafka import KafkaConsumer
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import json

bucket = "de-project"
org = "my-org"
token = "InitialAdminToken0=="

url = "localhost:8086"

client = influxdb_client.InfluxDBClient(
    url="http://influxdb:8086",
    token=token,
    org=org
)

write_api = client.write_api(write_options=SYNCHRONOUS)

def consume_and_process():
    consumer = KafkaConsumer(
        'sensor-data',
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

    for message in consumer:
        data = message.value
        print(data['timestamp']+' '+data['longitude'])
        point = influxdb_client.Point("athlete_data") \
            .tag('event', 'Frankfurt_Marathon') \
            .field('longitude', float(data['longitude'])) \
            .field('latitude', float(data['latitude'])) \
            .field('distance', float(data['distance_total'])) \
            .field('time_passed', float(data['time_passed'])) \
            .field('speed_current', float(data['speed_current'])) \
            .field('speed_avg', float(data['speed_avg'])) \
            .field('hr_current', int(data['heart_rate'])) \
            .field('hr_avg', float(data['hr_avg'])) \
            .field('elevation', float(data['elevation'])) \
            .time(data['timestamp'], write_precision='s')
        
        write_api.write(bucket=bucket, record=point)

if __name__ == '__main__':
    consume_and_process()
    