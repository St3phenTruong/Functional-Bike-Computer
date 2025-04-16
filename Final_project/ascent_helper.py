def calculate_ascent(current_pressure, pressure_history, previous_altitude, sea_level_pressure):
    """Calculate ascent based on pressure data."""
    # Add current pressure to history
    pressure_history.append(current_pressure)
    if len(pressure_history) > 5:  # Moving average filter
        pressure_history.pop(0)

    # Apply moving average filter
    filtered_pressure = sum(pressure_history) / len(pressure_history)

    # Calculate current altitude
    current_altitude = 44330 * (1.0 - (filtered_pressure / sea_level_pressure)**(1 / 5.255))

    # Skip if altitude is not initialized
    if previous_altitude is not None:
        altitude_change = current_altitude - previous_altitude
        if altitude_change > 1.0:  # Minimum altitude change threshold in meters
            return altitude_change, current_altitude
    return 0.0, current_altitude
