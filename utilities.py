from math import sin, cos, sqrt, atan2, radians

def stringify_latitude(latitude):

    lat_str = 'N'

    if latitude < 0:
        lat_str = 'S'
        latitude *= -1

    lat_str += str(latitude).zfill(3)
    return lat_str
    
def stringify_longitude(longitude):

    lon_str = 'E'

    if longitude < 0:
        lon_str = 'W'
        longitude *= -1

    lon_str += str(longitude).zfill(3)
    return lon_str
    
def string_to_position(str):

    str = str.split('_')[1]

    lat_str, lon_str = str[:4], str[4:]
    
    lat = 1
    if lat_str.startswith('S'):
        lat = -1
    
    lon = 1
    if lon_str.startswith('W'):
        lon = -1
        
    lat *= int(lat_str[1:])
    lon *= int(lon_str[1:])
    
    return lat, lon
    
    
def get_patch_dimensions(latitude):
    
    #latitude distance
    
    lat_distance = 111.0
    
    #longitude distance
    
    lat = radians(latitude)
    
    dlon = radians(0.5)

    a = sin(0 / 2)**2 + cos(lat)**2 * sin(dlon)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    lon_distance = 6373.0 * c
    
    return lat_distance, lon_distance
    

def calculate_distance(first_point,second_point):
    
    lat1 = radians(first_point[0])
    lon1 = radians(first_point[1])
    
    lat2 = radians(second_point[0])
    lon2 = radians(second_point[1])

    # approximate radius of earth in km
    R = 6373.0

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    
    return distance
