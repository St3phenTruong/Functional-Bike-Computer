from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer
import board
import busio
from datetime import datetime
from adafruit_bme280 import basic as adafruit_bme280
from heart_rate_thread import HeartRateThread  # Import the heart rate thread
from speed_helper import calculate_speed, haversine
from ascent_helper import calculate_ascent

class MetricTab(QWidget):
    def __init__(self, environment_sensor):
        super(MetricTab, self).__init__()
        # Store the environment sensor instance
        self.environment_sensor = environment_sensor

        # Initialize the BME280 sensor for barometric pressure
        self.i2c_bus = busio.I2C(board.SCL, board.SDA)  # Standard I2C pins
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c_bus, address=0x76)
        self.sea_level_pressure = 1013.25  # hPa, standard sea-level pressure

        self.gps_module = None
        self.previous_latitude = None  # Store previous latitude
        self.previous_longitude = None  # Store previous longitude
        self.previous_time = None  # Store previous timestamp
        self.speed = 0.0  # Initialize speed
        self.total_distance = 0.0  # Initialize total distance

        # Initialize variables for ascent calculation
        self.previous_altitude = None
        self.ascent = 0
        self.pressure_history = []  # For moving average filter

        # Create the layout for the first tab
        layout = QGridLayout()

        # Create multiple labels
        self.label1 = QLabel("POWER")
        self.label2 = QLabel()  # Unified heart rate label
        self.label3 = QLabel()  # Speed label updated below
        self.label4 = QLabel("CADENCE")
        self.label6 = QLabel()  # Distance label updated below
        self.label7 = QLabel("ENERGY")
        self.label8 = QLabel()  # Unified ascent label
        self.label9 = QLabel(" ")

        # Timer label
        self.timer_label = QLabel()
        self.update_timer_display(0, 0, 0)  # Initialize with "TIMER" title

        # Customize the fonts for each label
        font = QFont()
        font.setPointSize(15)

        for label in [self.label1, self.label2, self.label3, self.label4, self.timer_label,
                      self.label6, self.label7, self.label8]:
            label.setFont(font)
            label.setAlignment(Qt.AlignHCenter)
            label.setStyleSheet("border: 1px solid black;")

        # Set up the grid with labels
        layout.addWidget(self.label1, 0, 0)
        layout.addWidget(self.label2, 0, 2)  # Unified heart rate label
        layout.addWidget(self.label3, 1, 0)  # Speed label
        layout.addWidget(self.label4, 1, 1)
        layout.addWidget(self.timer_label, 1, 2)
        layout.addWidget(self.label6, 2, 0)  # Distance label
        layout.addWidget(self.label7, 2, 1)
        layout.addWidget(self.label8, 2, 2)  # Unified ascent label

        # Add an image to the label9 widget
        pixmap = QPixmap("/home/msi/prj/Final_project/biker.png")
        self.label9.setPixmap(pixmap)
        self.label9.setAlignment(Qt.AlignCenter)
        self.label9.setScaledContents(False)
        layout.addWidget(self.label9, 0, 1)

        # Set the layout for this widget
        self.setLayout(layout)

        # Start heart rate thread
        self.heart_rate_thread = HeartRateThread()
        self.heart_rate_thread.heart_rate_signal.connect(self.update_heart_rate)
        self.heart_rate_thread.start()

        # Start ascent update timer
        self.ascent_timer = QTimer()
        self.ascent_timer.timeout.connect(self.update_ascent)
        self.ascent_timer.start(1000)  # Update every 1 second

        # Start speed calculation
        self.start_speed_calculation()

    def set_gps_module(self, gps_module):
        self.gps_module = gps_module

    def get_gps_data(self):
        """Fetch GPS data from the module."""
        if not self.gps_module:
            print("GPS module not set")
            return None
        try:
            latitude = self.gps_module.latitude
            longitude = self.gps_module.longitude
            timestamp = datetime.now() if not hasattr(self.gps_module, 'timestamp') else self.gps_module.timestamp
            print(f"GPS Data: Latitude={latitude}, Longitude={longitude}, Timestamp={timestamp}")
            return latitude, longitude, timestamp
        except Exception as e:
            print(f"Error accessing GPS data: {e}")
            return None

    def update_speed_and_distance(self):
        gps_data = self.get_gps_data()
        if gps_data:
            latitude, longitude, timestamp = gps_data

            print(f"Current GPS Data: ({latitude}, {longitude}), Previous: ({self.previous_latitude}, {self.previous_longitude})")
            print(f"Timestamp: {timestamp}, Previous Time: {self.previous_time}")

            # Calculate speed
            self.speed = calculate_speed(self.previous_latitude, self.previous_longitude, self.previous_time, latitude, longitude, timestamp)
            print(f"Calculated Speed: {self.speed:.2f} km/h")

            # Calculate distance
            if self.previous_latitude is not None and self.previous_longitude is not None:
                distance = haversine(self.previous_latitude, self.previous_longitude, latitude, longitude)
                self.total_distance += distance
                print(f"Calculated Distance: {distance:.2f} km, Total Distance: {self.total_distance:.2f} km")

            # Update previous values
            self.previous_latitude = latitude
            self.previous_longitude = longitude
            self.previous_time = timestamp
        else:
            self.speed = 0.0
            print("No GPS data available for speed or distance calculation")

        # Update the speed label
        self.label3.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>SPEED</span><br>"
            f"<span style='font-size: 25px;'>{self.speed:.1f} km/h</span>"
            f"</div>"
        )

        # Update the distance label
        self.label6.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>DISTANCE</span><br>"
            f"<span style='font-size: 25px;'>{self.total_distance:.2f} km</span>"
            f"</div>"
        )

    def start_speed_calculation(self):
        """Start periodic speed and distance updates."""
        self.speed_timer = QTimer()
        self.speed_timer.timeout.connect(self.update_speed_and_distance)
        self.speed_timer.start(1000)  # Update every second

    def update_timer_display(self, hours, minutes, seconds):
        """Update the timer label display."""
        self.timer_label.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>TIMER</span><br>"
            f"<span style='font-size: 25px;'>{hours:02}:{minutes:02}:{seconds:02}</span>"
            f"</div>"
        )

    def update_ascent(self):
        """Update ascent value based on pressure changes."""
        current_pressure = self.bme280.pressure
        altitude_change, self.previous_altitude = calculate_ascent(current_pressure, self.pressure_history, self.previous_altitude, self.sea_level_pressure)

        if altitude_change > 0:
            self.ascent += altitude_change

        # Update the ascent label
        self.label8.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>ASCENT</span><br>"
            f"<span style='font-size: 25px;'>{self.ascent:.1f} m</span>"
            f"</div>"
        )

    def update_heart_rate(self, heart_rate):
        """Update the unified heart rate label."""
        self.label2.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>HEARTRATE</span><br>"
            f"<span style='font-size: 25px;'>{heart_rate} bpm</span>"
            f"</div>"
        )

    def closeEvent(self, event):
        """Handle cleanup when the widget is closed."""
        self.heart_rate_thread.stop()  # Stop the heart rate thread
        self.heart_rate_thread.wait()
        super().closeEvent(event)
