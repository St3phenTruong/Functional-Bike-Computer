import serial
import pynmea2

class LC76G:
    def __init__(self, port='/dev/ttyS0', baudrate=115200):
        """
        Initialize GPS module.
        Args:
            port (str): Serial port to connect to GPS module.
            baudrate (int): Baudrate for the serial connection.
        """
        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
        except serial.SerialException as e:
            print(f"Error initializing serial connection: {e}")
            self.serial = None

        self.latitude = None
        self.longitude = None
        self.timestamp = None

    def update(self):
        """
        Read and parse data from the GPS module.
        """
        if not self.serial or not self.serial.is_open:
            print("Serial port not initialized or not open.")
            return

        try:
            line = self.serial.readline().decode('ascii', errors='replace').strip()
            if line.startswith('$GNRMC'):  # Use GNRMC sentence for position and time
                msg = pynmea2.parse(line)
                if msg.status == 'A':  # 'A' means valid data
                    self.latitude = msg.latitude
                    self.longitude = msg.longitude
                    self.timestamp = msg.datetime
                    print(f"GPS Data Updated: Latitude={self.latitude}, Longitude={self.longitude}, Timestamp={self.timestamp}")
                else:
                    print("GPS data not valid.")
        except pynmea2.ParseError as e:
            print(f"NMEA Parse Error: {e}")
        except Exception as e:
            print(f"Error reading GPS data: {e}")

    def close(self):
        """
        Close the serial connection.
        """
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("Serial connection closed.")
