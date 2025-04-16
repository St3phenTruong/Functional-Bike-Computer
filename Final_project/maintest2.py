import time
import json
import requests
import serial
import threading
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData
from BME2801 import BME280

# ThingsBoard configuration
THINGSBOARD_HOST = "http://thingsboard.cloud"
ACCESS_TOKEN = "kF113LUmR6igJEro190R"  # Replace with your device token

# Shared variables for telemetry data
heart_rate = None
heart_rate_lock = threading.Lock()
stop_event = threading.Event()

# Function to convert latitude/longitude to decimal degrees
def convert_to_decimal(degrees, minutes, direction):
    decimal = degrees + (minutes / 60.0)
    if direction in ['S', 'W']:
        decimal = -decimal
    return round(decimal, 4)

# Function to parse NMEA sentence
def parse_nmea_sentence(nmea_sentence):
    parts = nmea_sentence.split(',')
    if len(parts) < 5:
        return None, None  # Not enough data

    if parts[0] == '$GNGGA' or parts[0] == '$GNGLL':
        try:
            lat = float(parts[1])
            lon = float(parts[3])
            lat_dir = parts[2]
            lon_dir = parts[4]

            lat_deg = int(lat / 100)
            lat_min = lat % 100
            lon_deg = int(lon / 100)
            lon_min = lon % 100

            latitude_decimal = convert_to_decimal(lat_deg, lat_min, lat_dir)
            longitude_decimal = convert_to_decimal(lon_deg, lon_min, lon_dir)

            return latitude_decimal, longitude_decimal
        except ValueError:
            return None, None

    return None, None

# Function to send telemetry using HTTP
def send_telemetry(data):
    url = f"{THINGSBOARD_HOST}/api/v1/{ACCESS_TOKEN}/telemetry"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            print("Data sent successfully!")
        else:
            print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Heart rate monitor thread
def heart_rate_monitor(node, heart_rate_device, stop_event):
    global heart_rate

    def on_found():
        print("Heart rate device found")

    def on_device_data(page, page_name, data):
        global heart_rate
        if isinstance(data, HeartRateData):
            with heart_rate_lock:
                heart_rate = data.heart_rate

    heart_rate_device.on_found = on_found
    heart_rate_device.on_device_data = on_device_data

    try:
        node.start()
        while not stop_event.is_set():
            time.sleep(1)
    finally:
        heart_rate_device.close_channel()
        node.stop()

# Main function
def main():
    # Initialize BME280 sensor
    sensor = BME280()
    sensor.get_calib_param()
    time.sleep(1)

    # Set up the serial connection for GPS
    serial_port = serial.Serial("/dev/ttyS0", baudrate=115200, timeout=1)

    # Initialize ANT+ node and heart rate device
    node = Node()
    node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
    heart_rate_device = HeartRate(node, device_id=0)

    # Start heart rate monitor thread
    heart_rate_thread = threading.Thread(target=heart_rate_monitor, args=(node, heart_rate_device, stop_event))
    heart_rate_thread.start()

    try:
        while True:
            # Read NMEA sentence from GPS
            try:
                nmea_sentence = serial_port.readline().decode('ascii', errors='replace').strip()
                latitude, longitude = parse_nmea_sentence(nmea_sentence)
            except Exception as e:
                latitude, longitude = None, None
                print(f"Error parsing NMEA: {e}")

            # Read BME280 sensor data
            try:
                pressure, temperature, humidity = sensor.readData()
            except Exception as e:
                pressure, temperature, humidity = None, None, None
                print(f"Error reading BME280: {e}")

            # Access heart rate data safely
            with heart_rate_lock:
                current_heart_rate = heart_rate

            # Prepare telemetry data
            data = {
                "latitude": latitude,
                "longitude": longitude,
                "pressure": pressure,
                "temperature": temperature,
                "humidity": humidity,
                "heart_rate": current_heart_rate
            }

            # Send telemetry to ThingsBoard
            send_telemetry(data)

            # Debug print
            print(f"Latitude: {latitude}, Longitude: {longitude}")
            print(f"Pressure: {pressure} hPa, Temperature: {temperature} °C, Humidity: {humidity} %")
            print(f"Heart Rate: {current_heart_rate} bpm")
            print("------------------------")

            time.sleep(1)  # Wait for 1 second before the next iteration

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        stop_event.set()
        heart_rate_thread.join()
        serial_port.close()

if __name__ == "__main__":
    main()
