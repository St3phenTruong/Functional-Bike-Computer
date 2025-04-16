import serial  # For reading GPS data over UART
import time
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl, QThread, pyqtSignal
import folium
import os
import board
import busio
import adafruit_icm20x
import math

class GPSDataThread(QThread):
    gps_signal = pyqtSignal(float, float)  # Signal to send latitude and longitude

    def __init__(self, serial_port):
        super(GPSDataThread, self).__init__()
        self.serial_port = serial_port
        self.running = True  # Control variable to stop the thread when needed

    def run(self):
        while self.running:
            try:
                line = self.serial_port.readline().decode('ascii', errors='replace')
                if line.startswith('$GNRMC'):
                    parts = line.split(',')
                    if parts[3] and parts[5] and parts[2] == 'A':
                        latitude = self.convert_to_decimal(parts[3], parts[4], lat=True)
                        longitude = self.convert_to_decimal(parts[5], parts[6], lat=False)
                        print(f"NMEA Sentence: {line.strip()}")
                        print(f"Latitude: {latitude:.6f}, Longitude: {longitude:.6f}")
                        self.gps_signal.emit(latitude, longitude)  # Emit new position
            except Exception as e:
                print(f"Error reading GPS data: {e}")

    def stop(self):
        self.running = False  # Method to stop the thread safely

    def convert_to_decimal(self, value, direction, lat):
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


class MapTab(QWidget):
    def __init__(self):
        super(MapTab, self).__init__()

        layout = QVBoxLayout()
        self.fallback_position = (16.0554087, 108.2042318)
        self.current_position = self.fallback_position  # Initialize with fallback position
        self.last_position = None  # Track last position for map reload checks

        # Set up serial connection to GPS module
        self.serial_port = serial.Serial(
            '/dev/ttyS0',  # Replace with your GPS module's UART port
            baudrate=115200,
            timeout=1
        )

        # Start GPS data thread
        self.gps_thread = GPSDataThread(self.serial_port)
        self.gps_thread.gps_signal.connect(self.update_position)
        self.gps_thread.start()

        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.setLayout(layout)

        # Load initial map with fallback position
        self.load_map(self.current_position)

        # Timer to update the map every 5 seconds if the position has changed
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.reload_map_if_needed)
        self.update_timer.start(5000)  # 5000 ms = 5 seconds

    def load_map(self, position):
        """Generates and loads the map based on a given position."""
        map_ = folium.Map(location=position, zoom_start=20)
        folium.Marker(position, tooltip="Current Position").add_to(map_)
        map_path = "map.html"
        map_.save(map_path)
        self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(map_path)))

    def update_position(self, latitude, longitude):
        """Receive GPS data and update current position."""
        self.current_position = (latitude, longitude)

    def reload_map_if_needed(self):
        """Reloads the map if the position has changed in the last 5 seconds."""
        if self.current_position != self.last_position:
            self.load_map(self.current_position)
            self.last_position = self.current_position  # Update last known position

    def closeEvent(self, event):
        """Handle cleanup when the widget is closed."""
        self.gps_thread.stop()  # Stop the GPS data thread
        self.gps_thread.wait()
        super().closeEvent(event)
