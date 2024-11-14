from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import time

# setting credentials for InfluxDB
bucket = "de-project"
org = "my-org"
token = "InitialAdminToken0=="
url = "http://influxdb:8086"

# establishing InfluxDB client and write API
client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)
write_api = client.write_api(write_options=SYNCHRONOUS)

def create_consumer(bootstrap_servers, retries=10, delay=5):
    # trying to connect to the Kafka brokers until they are finally available
    for attempt in range(retries):
        try:
            consumer = KafkaConsumer(
                'sensor-data',
                bootstrap_servers=bootstrap_servers,
                auto_offset_reset='earliest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            print("Connected to Kafka broker.")
            return consumer
        except NoBrokersAvailable:
            print(f"Attempt {attempt + 1}/{retries}: Kafka broker not available. Retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Could not connect to Kafka broker after multiple retries.")

def consume_and_process(consumer):
    # each datapoint equals a message and gets loaded to InfluxDB
    for message in consumer:
        data = message.value
        print(f"Processed datapoint: {data['timestamp']}") # print for debugging and terminal info
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
    consumer = create_consumer(['kafka1:9092','kafka2:9093'])
    consume_and_process(consumer)
