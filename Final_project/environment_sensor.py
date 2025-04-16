import time
import board
import busio
from adafruit_bme280 import basic as adafruit_bme280

class EnvironmentSensor:
    def __init__(self, i2c_address=0x76):
        # Initialize I2C and BME280 sensor
        i2c = busio.I2C(board.SCL, board.SDA)  # Use busio for I2C
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=i2c_address)

        # Optionally set up sea level pressure (adjust based on location)
        self.bme280.sea_level_pressure = 1013.25  # Default sea level pressure

        # Variables to store altitude data for ascent calculation
        self.previous_altitude = None
        self.total_ascent = 0.0

    def read_temperature(self):
        """Read temperature from the BME280 sensor."""
        return self.bme280.temperature  # Returns temperature in Celsius

    def read_humidity(self):
        """Read humidity from the BME280 sensor."""
        return self.bme280.humidity  # Returns humidity in percentage

    def read_pressure(self):
        """Read pressure from the BME280 sensor."""
        return self.bme280.pressure  # Returns pressure in hPa

    def get_altitude(self):
        """Calculate and return the current altitude based on pressure."""
        # Calculate altitude in meters using the barometric formula
        altitude = self.bme280.altitude
        return altitude

    def get_ascent(self):
        """
        Calculate and return the cumulative ascent based on altitude changes.
        Assumes small time intervals between readings for accurate ascent calculation.
        """
        current_altitude = self.get_altitude()

        # If this is the first reading, initialize previous_altitude
        if self.previous_altitude is None:
            self.previous_altitude = current_altitude
            return 0.0  # No ascent calculated on the first reading

        # Calculate altitude difference (positive if climbing, zero or negative otherwise)
        altitude_difference = current_altitude - self.previous_altitude
        if altitude_difference > 0:
            self.total_ascent += altitude_difference

        # Update the previous altitude for the next calculation
        self.previous_altitude = current_altitude
        return self.total_ascent

# Example usage:
if __name__ == "__main__":
    sensor = EnvironmentSensor()

    while True:
        temperature = sensor.read_temperature()
        humidity = sensor.read_humidity()
        pressure = sensor.read_pressure()
        altitude = sensor.get_altitude()
        ascent = sensor.get_ascent()

        print(f"Temperature: {temperature:.2f} °C")
        print(f"Humidity: {humidity:.2f} %")
        print(f"Pressure: {pressure:.2f} hPa")
        print(f"Altitude: {altitude:.2f} m")
        print(f"Total Ascent: {ascent:.2f} m")
        time.sleep(2)  # Read every 2 seconds
