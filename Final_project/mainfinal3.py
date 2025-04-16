from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt
import sys
import threading
import time
import requests
import json
from app_map import MapTab
from app_metric import MetricTab
from app_I2C import I2CTab
from gps_manager import GPSManager
from environment_sensor import EnvironmentSensor

# ThingsBoard configuration
THINGSBOARD_HOST = "http://thingsboard.cloud"
ACCESS_TOKEN = "kF113LUmR6igJEro190R"  # Replace with your device token

# Shared variables for telemetry data
heart_rate = None
heart_rate_lock = threading.Lock()
stop_event = threading.Event()

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

def telemetry_thread_function():
    global heart_rate
    gps_manager = GPSManager(port='/dev/ttyS0', baudrate=115200)
    environment_sensor = EnvironmentSensor()

    while not stop_event.is_set():
        # Collect telemetry data
        latitude, longitude = gps_manager.get_location()
        pressure, temperature, humidity = environment_sensor.read_data()

        with heart_rate_lock:
            current_heart_rate = heart_rate

        # Prepare telemetry data
        data = {
            "latitude": latitude,
            "longitude": longitude,
            "pressure": pressure,
            "temperature": temperature,
            "humidity": humidity,
            "heart_rate": current_heart_rate
        }

        # Send telemetry to ThingsBoard
        send_telemetry(data)

        # Debug print
        print(f"Latitude: {latitude}, Longitude: {longitude}")
        print(f"Pressure: {pressure} hPa, Temperature: {temperature} °C, Humidity: {humidity} %")
        print(f"Heart Rate: {current_heart_rate} bpm")
        print("------------------------")

        time.sleep(1)  # Wait for 1 second before the next iteration

class MainWindow(QMainWindow):
    def __init__(self, gps_manager, environment_sensor):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Group4_GPS_Cycling")
        self.resize(480, 310)

        main_layout = QVBoxLayout()
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)

        first_tab = MetricTab(gps_manager, environment_sensor)
        tabs.addTab(first_tab, "METRIC")

        second_tab = MapTab(gps_manager)
        tabs.addTab(second_tab, "MAP")

        third_tab = I2CTab()
        tabs.addTab(third_tab, "I2C")

        main_layout.addWidget(tabs)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer_running = False
        self.seconds_elapsed = 0

        button_row = QHBoxLayout()
        self.start_button = QPushButton("START")
        self.refresh_button = QPushButton("REFRESH")
        save_button = QPushButton("SAVE")
        delete_button = QPushButton("DELETE")

        start_icon = QIcon("/home/msi/prj/Final_project/icon/1.png")
        refresh_icon = QIcon("/home/msi/prj/Final_project/icon/4.png")
        save_icon = QIcon("/home/msi/prj/Final_project/icon/2.png")
        delete_icon = QIcon("/home/msi/prj/Final_project/icon/3.png")

        self.start_button.setIcon(start_icon)
        self.refresh_button.setIcon(refresh_icon)
        save_button.setIcon(save_icon)
        delete_button.setIcon(delete_icon)

        self.start_button.clicked.connect(self.toggle_timer)
        self.refresh_button.clicked.connect(self.reset_timer)

        button_row.addWidget(self.start_button)
        button_row.addWidget(save_button)
        button_row.addWidget(delete_button)
        button_row.addWidget(self.refresh_button)
        button_row.setAlignment(Qt.AlignCenter)

        main_layout.addLayout(button_row)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.metric_tab = first_tab

    def update_timer(self):
        self.seconds_elapsed += 1
        hours, remainder = divmod(self.seconds_elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.metric_tab.update_timer_display(hours, minutes, seconds)

    def toggle_timer(self):
        if self.timer_running:
            self.timer.stop()
            self.start_button.setText("START")
        else:
            self.timer.start(1000)
            self.start_button.setText("STOP")
        self.timer_running = not self.timer_running

    def reset_timer(self):
        self.timer.stop()
        self.timer_running = False
        self.seconds_elapsed = 0
        self.metric_tab.update_timer_display(0, 0, 0)
        self.start_button.setText("START")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gps_manager = GPSManager(port='/dev/ttyS0', baudrate=115200)
    environment_sensor = EnvironmentSensor()
    window = MainWindow(gps_manager, environment_sensor)
    window.show()

    # Start telemetry thread
    telemetry_thread = threading.Thread(target=telemetry_thread_function)
    telemetry_thread.start()

    try:
        sys.exit(app.exec_())
    finally:
        stop_event.set()
        telemetry_thread.join()