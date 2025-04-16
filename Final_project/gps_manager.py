from PyQt5.QtCore import QObject, QThread, pyqtSignal
import serial
import pynmea2


class GPSManager(QObject):
    gps_signal = pyqtSignal(float, float)  # Emit latitude, longitude

    def __init__(self, port='/dev/ttyS0', baudrate=115200):
        super().__init__()
        self.serial = None
        self.running = True
        self.latitude = None
        self.longitude = None

        try:
            self.serial = serial.Serial(port, baudrate, timeout=1)
            print(f"Serial connection established on {port} with baudrate {baudrate}.")
        except serial.SerialException as e:
            print(f"Error initializing serial connection: {e}")
            self.serial = None

        # Start a thread for reading GPS data
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self._read_data)
        self.thread.start()

    def _read_data(self):
        """Read GPS data continuously in the background thread."""
        while self.running:
            if not self.serial or not self.serial.is_open:
                continue
            try:
                line = self.serial.readline().decode('ascii', errors='replace').strip()
                if line.startswith('$GNRMC'):
                    msg = pynmea2.parse(line)
                    if msg.status == 'A':  # 'A' indicates valid data
                        self.latitude = msg.latitude
                        self.longitude = msg.longitude
                        print(f"GPS Data: Latitude={self.latitude}, Longitude={self.longitude}")
                        self.gps_signal.emit(self.latitude, self.longitude)
            except Exception as e:
                print(f"Error reading GPS data: {e}")

    def stop(self):
        """Stop the GPS manager and close the serial connection."""
        self.running = False
        self.thread.quit()
        self.thread.wait()
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("Serial connection closed.")
