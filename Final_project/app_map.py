from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QTimer, QUrl
import folium
import os

class MapTab(QWidget):
    def __init__(self, gps_manager):
        super(MapTab, self).__init__()
        self.gps_manager = gps_manager  # Use the shared GPSManager instance
        self.current_position = (16.0554087, 108.2042318)  # Fallback position
        self.last_position = None

        layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        self.setLayout(layout)

        # Load the initial map
        self.load_map(self.current_position)
        print(f"Initial map loaded at position: {self.current_position}")

        # Timer to update position every 5 seconds
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_and_update_position)
        self.update_timer.start(5000)  # 5 seconds

        # Connect GPS signal to update the current position
        self.gps_manager.gps_signal.connect(self.receive_position)

    def load_map(self, position):
        """Generate and load the map."""
        try:
            map_ = folium.Map(location=position, zoom_start=20)
            folium.Marker(position, tooltip="Current Position").add_to(map_)
            map_path = "map.html"
            map_.save(map_path)
            self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(map_path)))
            print(f"Map displayed at: {position}")
        except Exception as e:
            print(f"Error in load_map: {e}")

    def receive_position(self, latitude, longitude):
        """Receive position updates from GPSManager."""
        self.current_position = (latitude, longitude)

    def check_and_update_position(self):
        """Update the map only if the position has changed."""
        try:
            if self.current_position != self.last_position:
                self.load_map(self.current_position)
                self.last_position = self.current_position
                print(f"Map updated to position: {self.current_position}")
        except Exception as e:
            print(f"Error in check_and_update_position: {e}")
