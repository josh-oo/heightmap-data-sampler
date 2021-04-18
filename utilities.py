import rasterio
import numpy as np
from rasterio.warp import calculate_default_transform
from math import sin, cos, sqrt, atan2, radians

IMAGE_HEIGHT = 3600

INPUT_PROJECTION = 'EPSG:4326' # (WGS 84)
OUTPUT_PROJECTION = 'EPSG:3857' # (Web Mercator)
    
def get_target_pixel_dimensions(latitude,longitude):
    right_longitude = (((longitude+180)+1)%360)-180
    bounds = (longitude, latitude, right_longitude, latitude+1)
    transform, width, height = calculate_default_transform(
        INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), IMAGE_HEIGHT, *bounds)
        
    return width, height

def get_pixel_width(latitude):
    #Specs from https://www.eorc.jaxa.jp/ALOS/en/aw3d30/aw3d30v3.2_product_e_e1.2.pdf
    if latitude >= 80 or latitude <= -80:
        return 600
    if latitude >= 70 or latitude <= -70:
        return 1200
    if latitude >= 60 or latitude <= -60:
        return 1800
    #default
    return IMAGE_HEIGHT

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

def pixel_to_coordinates(latitude,longitude, points):

    right_longitude = (((longitude+180)+1)%360)-180
    bounds = (longitude, latitude, right_longitude, latitude+1)
    
    transform, width, height = calculate_default_transform(
        INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), 3600, *bounds)
    
    y = points[:,0]
    x = points[:,1]
    
    mercator_pos = rasterio.transform.xy(transform, x, y, offset='ul')
    
    lat_lon = rasterio.warp.transform(OUTPUT_PROJECTION, INPUT_PROJECTION, mercator_pos[0],  mercator_pos[1])
    
    return np.stack((lat_lon[1], lat_lon[0]), axis = 1)
