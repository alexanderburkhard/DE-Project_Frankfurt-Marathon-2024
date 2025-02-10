# Data-Engineering-Project-Frankfurt-Marathon
Data Engineering Streaming Project built on Docker, Kafka, InfluxDB and Grafana to visualize .gpx workout files in a dashboard on a real-time basis
<img width="1240" alt="Bildschirmfoto 2024-11-14 um 22 36 12" src="https://github.com/user-attachments/assets/92365285-f9dc-4620-b340-c3a4727cac18">

## Concept
The project is built on microservices, each deployed as a docker container and orchestrated with docker compose. The producer application `producer.py` iterates over a given .gpx workout file, that has been pulled from my Strava-Account, covering the 2024 Frankfurt Marathon. Each data point in the time-stamped workout is sent to the Kafka topic "sensor-data". The consumer application `consumer.py` iterates over the message queue and calculates speed data based on timestamps and geo-coordinates. It also determines averages for speed and hear rate readings before loading the data into InfluxDB. Finally, the data is visualized through Grafana. The folder `/grafana-data` is mounted to the container to prevent data loss for the dashboard setup and InfluxDB connection.

## Instructions
To run this project, ensure that the latest version of Docker is installed and running on your machine and run `$ docker compose up --built` in the command line of the projects root folder. Once all services are up and running, the live iterartion of the workout data can be viewed by accessing accessing Grafana through [localhost:3000](http://localhost:3000/). The iteration speed can be adjusted by changing the `iteration_factor` variable in `producer.py`.
