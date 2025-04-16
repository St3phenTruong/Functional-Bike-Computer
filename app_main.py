from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
import sys
from app_map import MapTab  # Import MapTab from app_map.py
from app_metric import MetricTab  # Import MetricTab from metric_tab.py
from app_I2C import I2CTab  # Import I2CTab from app_I2C.py
from lc76g import LC76G  # Import LC76G class
from environment_sensor import EnvironmentSensor  # Import EnvironmentSensor

class MainWindow(QMainWindow):
    start_signal = pyqtSignal()  # Signal to notify MetricTab to start calculations

    def __init__(self, gps_module):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Group4_GPS_Cycling")

        # Set the initial size of the main window
        self.resize(480, 310)

        # Initialize the EnvironmentSensor
        environment_sensor = EnvironmentSensor()

        # Create the main layout
        main_layout = QVBoxLayout()

        # Create the QTabWidget
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.West)

        # First tab (MetricTab) - pass the sensor instance
        first_tab = MetricTab(environment_sensor)
        first_tab.set_gps_module(gps_module)  # Set the GPS module for the MetricTab
        tabs.addTab(first_tab, "METRIC")

        # Second Tab (MapTab)
        second_tab = MapTab()
        tabs.addTab(second_tab, "MAP")

        # Third Tab (I2CTab)
        third_tab = I2CTab()
        tabs.addTab(third_tab, "I2C")

        # Add the tabs widget to the main layout
        main_layout.addWidget(tabs)

        # Timer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer_running = False
        self.seconds_elapsed = 0

        # Bottom buttons section
        button_row = QHBoxLayout()

        # Create buttons with custom icons
        self.start_button = QPushButton("START")
        self.refresh_button = QPushButton("REFRESH")
        save_button = QPushButton("SAVE")
        delete_button = QPushButton("DELETE")

        # Load custom icon images
        start_icon = QIcon("/home/msi/prj/Final_project/icon/1.png")
        refresh_icon = QIcon("/home/msi/prj/Final_project/icon/4.png")
        save_icon = QIcon("/home/msi/prj/Final_project/icon/2.png")
        delete_icon = QIcon("/home/msi/prj/Final_project/icon/3.png")

        # Set icons for the buttons
        self.start_button.setIcon(start_icon)
        self.refresh_button.setIcon(refresh_icon)
        save_button.setIcon(save_icon)
        delete_button.setIcon(delete_icon)

        # Connect button signals to slots
        self.start_button.clicked.connect(self.toggle_timer)
        self.refresh_button.clicked.connect(self.reset_timer)

        # Add the buttons to the button row layout
        button_row.addWidget(self.start_button)
        button_row.addWidget(save_button)
        button_row.addWidget(delete_button)
        button_row.addWidget(self.refresh_button)
        # Align the button row to the bottom
        button_row.setAlignment(Qt.AlignCenter)

        # Add button row to the main layout
        main_layout.addLayout(button_row)

        # Create a central widget and set the main layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Store reference to MetricTab for timer updates
        self.metric_tab = first_tab

    def update_timer(self):
        """Update the timer label with the elapsed time."""
        self.seconds_elapsed += 1
        hours, remainder = divmod(self.seconds_elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.metric_tab.update_timer_display(hours, minutes, seconds)  # Update the timer display in MetricTab

    def toggle_timer(self):
        """Start or stop the timer."""
        if self.timer_running:
            self.timer.stop()
            self.start_button.setText("START")
        else:
            self.timer.start(1000)  # Timer ticks every 1000 ms (1 second)
            self.start_button.setText("STOP")
        self.timer_running = not self.timer_running

    def reset_timer(self):
        """Reset the timer to zero."""
        self.timer.stop()
        self.timer_running = False
        self.seconds_elapsed = 0
        self.metric_tab.update_timer_display(0, 0, 0)  # Reset the timer display in MetricTab
        self.start_button.setText("START")

if __name__ == "__main__":
    # Ensure QApplication is initialized before creating any QWidget
    app = QApplication(sys.argv)

    # Initialize GPS module
    gps_module = LC76G(port='/dev/ttyS0', baudrate=115200)

    # Create and show the main window
    window = MainWindow(gps_module)
    window.show()

    # Create a timer to update GPS data periodically
    gps_update_timer = QTimer()
    gps_update_timer.timeout.connect(gps_module.update)
    gps_update_timer.start(1000)  # Update GPS every 1 second

    # Start the application event loop
    sys.exit(app.exec_())
