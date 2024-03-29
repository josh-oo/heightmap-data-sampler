import rasterio
import numpy as np
from rasterio.warp import calculate_default_transform, transform_bounds
from math import sin, cos, sqrt, atan2, radians
import geopy.distance

IMAGE_HEIGHT = 3600

INPUT_PROJECTION = 'EPSG:4326' # (WGS 84)
OUTPUT_PROJECTION = 'EPSG:3857' # (Web Mercator)

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
    
def get_file_paths(latitude,longitude):

    lat_str = stringify_latitude(latitude)
    lon_str = stringify_longitude(longitude)

    file_name = 'ALPSMLC30_'+lat_str+lon_str+'_DSM.tif'
    
    floor_lat = int(latitude/5)*5
    floor_lon = int(longitude/5)*5
    
    if latitude < 0:
        lat_to = floor_lat - 5
        first_lat = stringify_latitude(lat_to)
        second_lat = stringify_latitude(floor_lat)
    else:
        lat_to = floor_lat + 5
        first_lat = stringify_latitude(floor_lat)
        second_lat = stringify_latitude(lat_to)
    
    
    if longitude < 0:
        lon_to = floor_lon - 5
        first_lon = stringify_longitude(lon_to)
        second_lon = stringify_longitude(floor_lon)
    else:
        lon_to = floor_lon + 5
        first_lon = stringify_longitude(floor_lon)
        second_lon = stringify_longitude(lon_to)
    
    folder_name = first_lat+first_lon + '_' + second_lat +second_lon
    
    return file_name, folder_name
    
def get_bounds(latitude, longitude):
    right_longitude = (((longitude+180)+1)%360)-180
    return (longitude, latitude, right_longitude, latitude+1)

def pixel_to_coordinates(latitude,longitude, points):

    bounds = get_bounds(latitude,longitude)
    
    transform, width, height = calculate_default_transform(
        INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), 3600, *bounds)
    
    y = points[:,0]
    x = points[:,1]
    
    mercator_pos = rasterio.transform.xy(transform, x, y, offset='ul')
    
    lat_lon = rasterio.warp.transform(OUTPUT_PROJECTION, INPUT_PROJECTION, mercator_pos[0],  mercator_pos[1])
    
    return np.stack((lat_lon[1], lat_lon[0]), axis = 1)
    
    
def get_target_pixel_dimensions(latitude,longitude):

    bounds = get_bounds(latitude,longitude)
    
    transform, width, height = calculate_default_transform(
        INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), IMAGE_HEIGHT, *bounds)
        
    return width, height
    
def km_to_pixel(latitude,longitude, km):

    bounds = get_bounds(latitude,longitude)
    
    biggest_latitude = latitude
    if biggest_latitude > 0:
        biggest_latitude += 1
    
    lat_distance = geopy.distance.geodesic((biggest_latitude,longitude), (latitude,longitude)).km
    lon_distance = geopy.distance.geodesic((biggest_latitude,longitude), (biggest_latitude,bounds[2])).km
    
    lat_radius = km/lat_distance
    lon_radius = km/lon_distance
        
    lats = [biggest_latitude-lat_radius]
    lons = [longitude+lon_radius]
    
    transform, width, height = calculate_default_transform(
    INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), IMAGE_HEIGHT, *bounds)
    
    lat_lon = rasterio.warp.transform(INPUT_PROJECTION, OUTPUT_PROJECTION, lons,  lats)
    
    pixel_positions = rasterio.transform.rowcol(transform,lat_lon[0],lat_lon[1])
    
    
    return int((pixel_positions[0] + pixel_positions[1])/2)
