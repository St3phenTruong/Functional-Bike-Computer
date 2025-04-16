from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from environment_sensor import EnvironmentSensor  # Assuming this is your sensor reading file

class I2CTab(QWidget):
    def __init__(self):
        super(I2CTab, self).__init__()

        # Initialize the environment sensor
        self.sensor = EnvironmentSensor()

        # Create the main grid layout for the tab
        layout = QGridLayout()

        # Temperature display
        self.temperature_display = QLabel()
        self.temperature_display.setAlignment(Qt.AlignCenter)
        self.temperature_display.setStyleSheet("border: 1px solid black; padding: 10px;")
        
        # Humidity display
        self.humidity_display = QLabel()
        self.humidity_display.setAlignment(Qt.AlignCenter)
        self.humidity_display.setStyleSheet("border: 1px solid black; padding: 10px;")

        # Pressure display
        self.pressure_display = QLabel()
        self.pressure_display.setAlignment(Qt.AlignCenter)
        self.pressure_display.setStyleSheet("border: 1px solid black; padding: 10px;")

        # Customize font size for the combined label and data display
        font_display = self.temperature_display.font()
        font_display.setPointSize(18)
        self.temperature_display.setFont(font_display)
        self.humidity_display.setFont(font_display)
        self.pressure_display.setFont(font_display)

        # Add widgets to layout with a border around each section
        layout.addWidget(self.temperature_display, 0, 0)
        layout.addWidget(self.humidity_display, 1, 0)
        layout.addWidget(self.pressure_display, 2, 0)

        # Set layout margins and spacing
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Set the layout for the tab
        self.setLayout(layout)

        # Initialize and start the update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_sensor_data)
        self.timer.start(1000)  # Update every 1000 ms (1 second)

        # Initial data load
        self.update_sensor_data()

    def update_sensor_data(self):
        """Retrieve and display sensor data with labels."""
        # Read sensor data
        temperature = self.sensor.read_temperature()
        humidity = self.sensor.read_humidity()
        pressure = self.sensor.read_pressure()

        # Update each display with label and data in one line
        self.temperature_display.setText(f"<b>TEMPERATURE</b><br>{temperature:.2f} °C")
        self.humidity_display.setText(f"<b>HUMIDITY</b><br>{humidity:.2f} %")
        self.pressure_display.setText(f"<b>PRESSURE</b><br>{pressure:.2f} hPa")
