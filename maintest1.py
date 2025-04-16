import time
import json
import requests
import serial
import threading
from gpstest import parse_nmea_sentence
from BME2801 import BME280
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData

# ThingsBoard configuration
THINGSBOARD_HOST = "http://thingsboard.cloud"
ACCESS_TOKEN = "kF113LUmR6igJEro190R"

# Shared variable for heart rate
heart_rate = None
heart_rate_lock = threading.Lock()

# Event to stop threads
stop_event = threading.Event()

# Function to send telemetry data to ThingsBoard
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

def heart_rate_monitor(node, heart_rate_device, stop_event):
    global heart_rate

    def on_found():
        print(f"Device {heart_rate_device} found and receiving")

    def on_device_data(page: int, page_name: str, data):
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

    # Start heart rate monitor in a separate thread
    heart_rate_thread = threading.Thread(target=heart_rate_monitor, args=(node, heart_rate_device, stop_event))
    heart_rate_thread.start()

    try:
        # Directly process and send data without waiting for manual intervention
        while True:
            # Read GPS data
            try:
                nmea_sentence = serial_port.readline().decode('ascii', errors='replace').strip()
                latitude, longitude = parse_nmea_sentence(nmea_sentence)
            except Exception as e:
                latitude, longitude = None, None  # Default values if GPS fails
                print(f"Error parsing NMEA: {e}")

            # Read BME280 data
            try:
                pressure, temperature, humidity = sensor.readData()
            except Exception as e:
                pressure, temperature, humidity = None, None, None
                print(f"Error reading BME280: {e}")

            # Access heart rate safely
            with heart_rate_lock:
                current_heart_rate = heart_rate

            # Prepare data payload
            data = {
                "latitude": latitude,
                "longitude": longitude,
                "pressure": pressure,
                "temperature": temperature,
                "humidity": humidity,
                "heart_rate": current_heart_rate  # Include heart rate in the data payload
            }

            # Send data to ThingsBoard
            send_telemetry(data)

            # Print data for debugging
            print(f"Latitude: {latitude}, Longitude: {longitude}")
            print(f"Pressure: {pressure} hPa, Temperature: {temperature} °C, Humidity: {humidity} %")
            print(f"Heart Rate: {current_heart_rate} bpm")
            print("------------------------")

            time.sleep(1)  # Update every second

    except KeyboardInterrupt:
        print("Exiting main loop...")
    finally:
        stop_event.set()  # Signal all threads to stop
        heart_rate_thread.join()  # Wait for thread to finish
        serial_port.close()

if __name__ == '__main__':
    main()
