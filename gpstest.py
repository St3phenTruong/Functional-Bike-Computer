import serial
import json
import requests

# ThingsBoard configuration
THINGSBOARD_HOST = "http://thingsboard.cloud"  # Ensure this URL is correct
ACCESS_TOKEN = "EXjWcFsI2iHv9BQF2F09"  # Replace with your device token

# Function to convert latitude/longitude to decimal degrees
def convert_to_decimal(degrees, minutes, direction):
    decimal = degrees + (minutes / 60.0)
    if direction in ['S', 'W']:
        decimal = -decimal
    return round(decimal, 4)

# Function to send telemetry using HTTP
def send_telemetry_http(latitude, longitude):
    url = "http://thingsboard.cloud/api/v1/EXjWcFsI2iHv9BQF2F09/telemetry"
    headers = {'Content-Type': 'application/json'}
    data = {
        "latitude": latitude,
        "longitude": longitude
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print("Data sent successfully!")
    else:
        print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")

# Function to parse NMEA sentence and extract latitude and longitude
def parse_nmea_sentence(nmea_sentence):
    parts = nmea_sentence.split(',')
    
    if len(parts) < 5:
        print(f"Not enough data in sentence: {nmea_sentence}")
        return None, None  # Not enough data
    
    #print(f"Parsing parts: {parts}")

    if parts[0] == '$GNGGA':
        try:
            lat = float(parts[1])
            lon = float(parts[3])
            lat_dir = parts[2]
            lon_dir = parts[4]

            # Convert latitude and longitude to degrees and minutes
            lat_deg = int(lat / 100)
            lat_min = lat % 100
            lon_deg = int(lon / 100)
            lon_min = lon % 100

            latitude_decimal = convert_to_decimal(lat_deg, lat_min, lat_dir)
            longitude_decimal = convert_to_decimal(lon_deg, lon_min, lon_dir)
            
            return latitude_decimal, longitude_decimal
        
        except ValueError:
            print(f"ValueError while parsing GNGGA: {nmea_sentence}")
            return None, None

    elif parts[0] == '$GNGLL':
        try:
            lat = float(parts[1])
            lon = float(parts[3])
            lat_dir = parts[2]
            lon_dir = parts[4]

            # Convert latitude and longitude to degrees and minutes
            lat_deg = int(lat / 100)
            lat_min = lat % 100
            lon_deg = int(lon / 100)
            lon_min = lon % 100

            latitude_decimal = convert_to_decimal(lat_deg, lat_min, lat_dir)
            longitude_decimal = convert_to_decimal(lon_deg, lon_min, lon_dir)
            
            return latitude_decimal, longitude_decimal
        
        except ValueError:
            print(f"ValueError while parsing GNGLL: {nmea_sentence}")
            return None, None

    print(f"Unsupported sentence: {nmea_sentence}")
    return None, None

# Set up the serial connection (check baudrate for your GPS module, usually 9600)
serial_port = serial.Serial("/dev/ttyS0", baudrate=115200, timeout=1)

# Main loop to read GPS data and send to ThingsBoard
while True:
    try:
        # Read a line from the serial port
        nmea_sentence = serial_port.readline().decode('ascii', errors='replace').strip()
        
        # Print raw NMEA sentence for debugging
        #print(f"Raw NMEA: {nmea_sentence}")

        # Parse the NMEA sentence and extract latitude and longitude
        latitude, longitude = parse_nmea_sentence(nmea_sentence)
        
        if latitude is not None and longitude is not None:
            print(f"Latitude: {latitude}, Longitude: {longitude}")
            
            # Send latitude and longitude to ThingsBoard
            send_telemetry_http(latitude, longitude)

    except KeyboardInterrupt:
        print("Exiting...")
        serial_port.close()
        break

# Close the serial port when done
#serial_port
