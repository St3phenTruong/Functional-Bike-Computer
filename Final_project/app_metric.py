from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime
from adafruit_bme280 import basic as adafruit_bme280  # Import BME280
from heart_rate_thread import HeartRateThread  # Import the heart rate thread
from speed_helper import calculate_speed, haversine
from ascent_helper import calculate_ascent
import board
import busio

class MetricTab(QWidget):
    def __init__(self, gps_manager, environment_sensor):
        super(MetricTab, self).__init__()
        self.gps_manager = gps_manager  # Use the shared GPSManager instance
        self.environment_sensor = environment_sensor  # Sensor instance

        # Initialize the BME280 sensor for barometric pressure
        self.i2c_bus = busio.I2C(board.SCL, board.SDA)  # Standard I2C pins
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(self.i2c_bus, address=0x76)
        self.sea_level_pressure = 1013.25  # hPa, standard sea-level pressure

        self.speed = 0.0
        self.total_distance = 0.0
        self.previous_latitude = None
        self.previous_longitude = None
        self.previous_time = None
        self.ascent = 0
        self.previous_altitude = None
        self.pressure_history = []  # Moving average filter for pressure

        # Initialize timer variables
        self.timer_running = False
        self.seconds_elapsed = 0

        # Create layout and labels
        layout = QGridLayout()

        self.label_heart_rate = QLabel()
        self.label_speed = QLabel()
        self.label_distance = QLabel()
        self.label_ascent = QLabel()
        self.timer_label = QLabel()

        # Customize label fonts
        font = QFont()
        font.setPointSize(15)
        for label in [self.label_heart_rate, self.label_speed, self.label_distance, self.label_ascent, self.timer_label]:
            label.setFont(font)
            label.setAlignment(Qt.AlignHCenter)
            label.setStyleSheet("border: 1px solid black;")

        # Set default values for labels
        self.label_heart_rate.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>HEARTRATE</span><br>"
            f"<span style='font-size: 25px;'>0 bpm</span>"
            f"</div>"
        )

        self.label_speed.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>SPEED</span><br>"
            f"<span style='font-size: 25px;'>0.0 km/h</span>"
            f"</div>"
        )

        self.label_distance.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>DISTANCE</span><br>"
            f"<span style='font-size: 25px;'>0.00 km</span>"
            f"</div>"
        )

        self.label_ascent.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>ASCENT</span><br>"
            f"<span style='font-size: 25px;'>0.0 m</span>"
            f"</div>"
        )

        self.timer_label.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>TIMER</span><br>"
            f"<span style='font-size: 25px;'>00:00:00</span>"
            f"</div>"
        )

        # Arrange labels in the grid layout
        layout.addWidget(self.label_heart_rate, 0, 0)
        layout.addWidget(self.timer_label, 2, 0, 1, 2)
        layout.addWidget(self.label_speed, 1, 0)
        layout.addWidget(self.label_distance, 1, 1)
        layout.addWidget(self.label_ascent, 0, 1)

        # Add a placeholder image for aesthetics
        pixmap = QPixmap("/home/msi/prj/Final_project/biker.png")
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label, 3, 0, 1, 2)

        self.setLayout(layout)

        # Connect GPSManager signal to update method
        self.gps_manager.gps_signal.connect(self.update_speed_and_distance)

        # Timer for updating ascent
        self.ascent_timer = QTimer()
        self.ascent_timer.timeout.connect(self.update_ascent)
        self.ascent_timer.start(1000)

        # Timer for updating elapsed time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        # Start the heart rate thread
        self.heart_rate_thread = HeartRateThread()
        self.heart_rate_thread.heart_rate_signal.connect(self.update_heart_rate)
        self.heart_rate_thread.start()

    def update_speed_and_distance(self, latitude, longitude):
        """Calculate speed and distance based on GPS data."""
        timestamp = datetime.now()
        if latitude is not None and longitude is not None:
            if self.previous_latitude is not None and self.previous_longitude is not None:
                distance = haversine(self.previous_latitude, self.previous_longitude, latitude, longitude)
                self.total_distance += distance
                self.speed = calculate_speed(self.previous_latitude, self.previous_longitude, self.previous_time, latitude, longitude, timestamp)

            self.previous_latitude = latitude
            self.previous_longitude = longitude
            self.previous_time = timestamp

            self.label_speed.setText(
                f"<div style='text-align: center;'>"
                f"<span style='font-size: 25px;'>SPEED</span><br>"
                f"<span style='font-size: 25px;'>{self.speed:.1f} km/h</span>"
                f"</div>"
            )

            self.label_distance.setText(
                f"<div style='text-align: center;'>"
                f"<span style='font-size: 25px;'>DISTANCE</span><br>"
                f"<span style='font-size: 25px;'>{self.total_distance:.2f} km</span>"
                f"</div>"
            )

    def update_ascent(self):
        """Update ascent value based on barometric pressure."""
        current_pressure = self.bme280.pressure
        altitude_change, self.previous_altitude = calculate_ascent(
            current_pressure,
            self.pressure_history,
            self.previous_altitude,
            self.sea_level_pressure
        )
        if altitude_change > 0:
            self.ascent += altitude_change

        self.label_ascent.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>ASCENT</span><br>"
            f"<span style='font-size: 25px;'>{self.ascent:.1f} m</span>"
            f"</div>"
        )

    def update_timer(self):
        """Update the timer display."""
        self.seconds_elapsed += 1
        hours, remainder = divmod(self.seconds_elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.update_timer_display(hours, minutes, seconds)

    def update_timer_display(self, hours, minutes, seconds):
        """Update the timer label display."""
        self.timer_label.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>TIMER</span><br>"
            f"<span style='font-size: 25px;'>{hours:02}:{minutes:02}:{seconds:02}</span>"
            f"</div>"
        )

    def update_heart_rate(self, heart_rate):
        """Update the unified heart rate label."""
        self.label_heart_rate.setText(
            f"<div style='text-align: center;'>"
            f"<span style='font-size: 25px;'>HEARTRATE</span><br>"
            f"<span style='font-size: 25px;'>{heart_rate} bpm</span>"
            f"</div>"
        )

    def start_timer(self):
        """Start the elapsed time timer."""
        self.timer.start(1000)  # Update every second
        self.timer_running = True

    def stop_timer(self):
        """Stop the elapsed time timer."""
        self.timer.stop()
        self.timer_running = False

    def reset_timer(self):
        """Reset the elapsed time timer."""
        self.timer.stop()
        self.timer_running = False
        self.seconds_elapsed = 0
        self.update_timer_display(0, 0, 0)

    def closeEvent(self, event):
        """Handle cleanup when the widget is closed."""
        self.heart_rate_thread.stop()  # Stop the heart rate thread
        self.heart_rate_thread.wait()
        self.gps_manager.stop()  # Stop the GPS manager
        super().closeEvent(event)
