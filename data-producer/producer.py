from lxml import etree
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from datetime import timedelta, date, datetime
import time
import json
from geopy import distance


# looping through the gpx file and extracting the all necessary workout information
def extract_gpx(gpx_path):
    tree = etree.parse(gpx_path)
    root = tree.getroot()
    ns = {'default': 'http://www.topografix.com/GPX/1/1',
        'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'}
    trkpts = root.findall('.//default:trkpt', namespaces=ns)
    data_points = []
    
    # each trackpoint consists of geo-location, HR, elevation and timestamp
    for trkpt in trkpts:
        lat = trkpt.get('lat')
        lon = trkpt.get('lon')
        time_elem = trkpt.find('default:time', namespaces=ns)
        ele_elem = trkpt.find('default:ele', namespaces=ns)
        hr_elem = trkpt.find('.//gpxtpx:hr', namespaces=ns)
    
        if time_elem is not None and hr_elem is not None:
            timestamp = time_elem.text
            elevation = ele_elem.text
            heart_rate = hr_elem.text
            data_points.append({
                'timestamp': timestamp,
                'latitude': lat,
                'longitude': lon,
                'elevation': elevation,
                'heart_rate': heart_rate
            })

    return data_points

# iterating through all data points and sending these to the designated topic
def iterate_workout(producer, topic, data_points):
    print('start iteration')

    prev_timestamp = None
    prev_geo = None
    distance_total = 0
    distance_point = 0
    
    speed_point = 0
    speed_rolling = []
    speed_current = 0

    hr_avg = 0
    
    time_passed = 0
    sleep_time = 0

    for data in data_points:
        current_timestamp = datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
        current_geo = (data['latitude'], data['longitude'])
        if prev_timestamp is not None:
            sleep_time = (current_timestamp - prev_timestamp).total_seconds() 
            time.sleep(max(sleep_time/20, 0)) # speeding up the iteration by factor 20 for demonstration purposes

        if prev_geo is not None:
            # getting distance between datapoints in km
            distance_point = distance.distance(prev_geo, current_geo).km 
            if sleep_time != 0:
                # calculating km/h for last trackpoint
                speed_point = distance_point/(sleep_time/3600)
                # smoothing the current speed by taking average of the last 10 data points (should equal 10s)
                if len(speed_rolling) >= 10:
                    # slicing the list to remove the oldest data point
                    speed_rolling = speed_rolling[1:] 
                 # appending the latest one
                speed_rolling.append(speed_point)
                speed_current = round(sum(speed_rolling)/len(speed_rolling),2)

        time_passed += sleep_time
        distance_total += distance_point
        
        if time_passed == 0:
            # speed starts at 0
            speed_avg = 0 
            # if the workout just started first reading is the average
            hr_avg = float(data['heart_rate']) 
        else:
            # calculating avg km/h based on time and distance passed so far
            speed_avg = distance_total/(time_passed/3600) 
            # calculating HR avg
            hr_avg = (hr_avg*(time_passed-sleep_time)/time_passed)+(float(data['heart_rate'])*sleep_time/time_passed)

        prev_timestamp = current_timestamp
        prev_geo = current_geo
        
        data['time_passed'] = time_passed
        data['distance_total'] = distance_total
        data['speed_current'] = speed_current
        data['speed_avg'] = speed_avg
        data['hr_avg'] = round(hr_avg,2)
        
        producer.send(topic, value=data)
        producer.flush()

def create_producer(bootstrap_servers, retries=10, delay=5):
    # trying to connect to the Kafka brokers until they are finally available
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Connected to Kafka broker.")
            return producer
        except NoBrokersAvailable:
            print(f"Attempt {attempt + 1}/{retries}: Kafka broker not available. Retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception("Could not connect to Kafka broker after multiple retries.")

file = '/data-producer/gpx_files/FFM_Marathon_2024.gpx'

if __name__ == "__main__":
    producer = create_producer(['kafka1:9092','kafka2:9093'])
    iterate_workout(producer, 'sensor-data', extract_gpx(file))
