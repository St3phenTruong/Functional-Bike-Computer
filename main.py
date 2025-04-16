import time
import json
import requests
import serial
from gpstest import parse_nmea_sentence, send_telemetry_http
from BME2801 import BME280

# ThingsBoard configuration
THINGSBOARD_HOST = "http://thingsboard.cloud"
ACCESS_TOKEN = "EXjWcFsI2iHv9BQF2F09"

# Function to send telemetry data to ThingsBoard
def send_telemetry(data):
    url = f"{THINGSBOARD_HOST}/api/v1/{ACCESS_TOKEN}/telemetry"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print("Data sent successfully!")
    else:
        print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")

def main():
    # Initialize BME280 sensor
    sensor = BME280()
    sensor.get_calib_param()
    time.sleep(1)

    # Set up the serial connection for GPS (check baudrate for your GPS module, usually 9600)
    serial_port = serial.Serial("/dev/ttyS0", baudrate=115200, timeout=1)

    try:
        while True:
            # Read GPS data
            nmea_sentence = serial_port.readline().decode('ascii', errors='replace').strip()
            latitude, longitude = parse_nmea_sentence(nmea_sentence)

            # Read BME280 data
            pressure, temperature, humidity = sensor.readData()

            # Prepare data payload
            data = {
                "latitude": latitude,
                "longitude": longitude,
                "pressure": pressure,
                "temperature": temperature,
                "humidity": humidity
            }

            # Send data to ThingsBoard
            send_telemetry(data)

            # Print data for debugging
            print(f"Latitude: {latitude}, Longitude: {longitude}")
            print(f"Pressure: {pressure} hPa, Temperature: {temperature} °C, Humidity: {humidity} %")
            print("------------------------")

            time.sleep(1)  # Update every second

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Close the serial port when done
        serial_port.close()

if __name__ == '__main__':
    main()

