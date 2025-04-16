from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth.
    Returns distance in kilometers.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0.0  # Return 0 if any coordinate is missing

    r = 6371  # Earth radius in kilometers
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c  # Distance in kilometers


def calculate_speed(
    previous_latitude, previous_longitude, previous_time, 
    latitude, longitude, timestamp, 
    distance_threshold=0.005, speed_threshold=0.5
):
    """
    Calculate speed based on GPS data with noise filtering.
    - Filters small changes in coordinates below `distance_threshold` (in km).
    - Ignores speed below `speed_threshold` (in km/h).
    """
    try:
        if previous_latitude is not None and previous_longitude is not None and previous_time is not None:
            # Calculate distance using Haversine formula
            distance = haversine(previous_latitude, previous_longitude, latitude, longitude)
            
            # Ignore distances below threshold (to filter GPS noise)
            if distance < distance_threshold:
                return 0.0
            
            # Calculate time difference in hours
            time_diff = (timestamp - previous_time).total_seconds() / 3600
            if time_diff > 0:
                speed = distance / time_diff  # Speed in km/h
                
                # Ignore speeds below threshold
                if speed < speed_threshold:
                    return 0.0
                
                return speed
    except Exception as e:
        print(f"Error in calculate_speed: {e}")
    
    # Return 0 if no valid speed could be calculated
    return 0.0


def calculate_distance(
    previous_latitude, previous_longitude, latitude, longitude, 
    total_distance, previous_time, timestamp, 
    distance_threshold=0.005, speed_threshold=0.5
):
    """
    Calculate total distance traveled with noise filtering.
    - Filters small changes in coordinates below `distance_threshold` (in km).
    - Ensures that distance is only added when valid speed (above `speed_threshold`) is detected.
    """
    try:
        if previous_latitude is not None and previous_longitude is not None and previous_time is not None:
            # Calculate distance
            distance = haversine(previous_latitude, previous_longitude, latitude, longitude)
            
            # Ignore distances below threshold (to filter GPS noise)
            if distance >= distance_threshold:
                # Calculate time difference in hours
                time_diff = (timestamp - previous_time).total_seconds() / 3600
                if time_diff > 0:
                    speed = distance / time_diff  # Speed in km/h
                    
                    # Only add distance if speed is valid
                    if speed >= speed_threshold:
                        total_distance += distance
    except Exception as e:
        print(f"Error in calculate_distance: {e}")
    
    return total_distance
