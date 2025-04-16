import serial

def convert_to_decimal(value, direction, lat):
    """Converts GPS NMEA latitude/longitude format to decimal."""
    if lat:
        degrees = int(value[:2])
        minutes = float(value[2:])
    else:
        degrees = int(value[:3])
        minutes = float(value[3:])
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_gps_data():
    """Fetch and parse GNRMC sentence for GPS coordinates."""
    # Set up serial connection to GPS module
    serial_port = serial.Serial(
        '/dev/ttyS0',  # Replace with your GPS module's UART port
        baudrate=115200,
        timeout=1
    )

    while True:
        try:
            line = serial_port.readline().decode('ascii', errors='replace').strip()
            
            if line.startswith('$GNRMC'):
                parts = line.split(',')
                if parts[3] and parts[5] and parts[2] == 'A':  # Check for valid data
                    latitude = convert_to_decimal(parts[3], parts[4], lat=True)
                    longitude = convert_to_decimal(parts[5], parts[6], lat=False)
                    print(f"Latitude: {latitude:.6f}, Longitude: {longitude:.6f}")
                else:
                    print("Invalid GPS data in GNRMC sentence.")
        except Exception as e:
            print(f"Error reading GPS data: {e}")

if __name__ == "__main__":
    get_gps_data()
