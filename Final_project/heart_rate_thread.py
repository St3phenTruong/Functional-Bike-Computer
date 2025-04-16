from PyQt5.QtCore import QThread, pyqtSignal
from openant.easy.node import Node
from openant.devices import ANTPLUS_NETWORK_KEY
from openant.devices.heart_rate import HeartRate, HeartRateData


class HeartRateThread(QThread):
    heart_rate_signal = pyqtSignal(int)  # Signal to emit heart rate updates

    def __init__(self, device_id=0):
        super(HeartRateThread, self).__init__()
        self.device_id = device_id
        self.running = True  # Control thread execution

    def run(self):
        node = Node()

        try:
            # Set network key with timeout handling
            print("Setting ANT+ network key...")
            node.set_network_key(0x00, ANTPLUS_NETWORK_KEY)
            print("Network key set successfully.")

            # Initialize the heart rate device
            device = HeartRate(node, device_id=self.device_id)

            def on_found():
                print(f"Device {device} found and receiving data.")

            def on_device_data(page: int, page_name: str, data):
                if isinstance(data, HeartRateData):
                    print(f"Heart rate update: {data.heart_rate} bpm")
                    self.heart_rate_signal.emit(data.heart_rate)

            device.on_found = on_found
            device.on_device_data = on_device_data

            # Start the node
            print("Starting heart rate monitoring...")
            node.start()

            while self.running:
                self.msleep(100)  # Avoid high CPU usage by sleeping briefly

        except Exception as e:
            print(f"Heart rate monitoring error: {e}")
        finally:
            # Clean up resources
            try:
                print("Closing device channel...")
                device.close_channel()
            except Exception as e:
                print(f"Error while closing device channel: {e}")
            try:
                print("Stopping node...")
                node.stop()
            except Exception as e:
                print(f"Error while stopping node: {e}")

    def stop(self):
        """Stop the thread safely."""
        self.running = False
