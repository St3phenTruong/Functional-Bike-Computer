import time
import board
import busio
import adafruit_icm20x

# Initialize I2C connection
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the ICM20948 sensor with the correct I2C address
sensor = adafruit_icm20x.ICM20948(i2c, address=0x68)

# Test reading accelerometer and magnetometer data
try:
    while True:
        # Accelerometer data (in m/s^2)
        accel_x, accel_y, accel_z = sensor.acceleration
        print(f"Accelerometer - X: {accel_x:.2f} m/s², Y: {accel_y:.2f} m/s², Z: {accel_z:.2f} m/s²")

        # Magnetometer data (in microteslas, µT)
        mag_x, mag_y, mag_z = sensor.magnetic
        print(f"Magnetometer - X: {mag_x:.2f} µT, Y: {mag_y:.2f} µT, Z: {mag_z:.2f} µT")

        # Wait a bit before reading again
        time.sleep(1)

except KeyboardInterrupt:
    print("Test stopped by user.")
