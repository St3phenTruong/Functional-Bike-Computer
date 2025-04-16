import time
from BME280 import BME280
from gpstest import parse_nmea_sentence, send_telemetry_http
import serial

# Initialize the BME280 sensor
bme280_sensor = BME280()
bme280_sensor.get_calib_param()

# Set up the serial connection for GPS (check baudrate for your GPS module, usually 9600)
serial_port = serial.Serial("/dev/ttyS0", baudrate=115200, timeout=1)

def main():
    while True:
        try:
            # Read a line from the serial port for GPS data
            nmea_sentence = serial_port.readline().decode('ascii', errors='replace').strip()
            print(f"Raw NMEA: {nmea_sentence}")

            # Parse the NMEA sentence and extract latitude and longitude
            latitude, longitude = parse_nmea_sentence(nmea_sentence)

            # Read data from the BME280 sensor
            pressure, temperature, humidity = bme280_sensor.readData()

            if latitude is not None and longitude is not None:
                print(f"Latitude: {latitude}, Longitude: {longitude}")
                print(f"Pressure: {pressure:.2f} hPa, Temperature: {temperature:.2f} °C, Humidity: {humidity:.2f} %")

                # Send combined data to ThingsBoard
                data = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "pressure": pressure,
                    "temperature": temperature,
                    "humidity": humidity
                }
                send_telemetry_http(data)

            # Wait for a short period before the next reading
            time.sleep(1)

        except KeyboardInterrupt:
            print("Exiting...")
            break

if _name_ == '_main_':
    main()