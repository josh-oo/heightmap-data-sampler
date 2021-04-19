import time
from PIL import ImageDraw, Image
import os

#from utilities import km_to_pixel
from process_images import get_image, get_file_paths, get_pixel_width
import math

import rasterio
from rasterio.warp import calculate_default_transform, transform_bounds

import geopy.distance

PATH_TO_DATASET = '/Volumes/Extreme SSD/Datasets/Terrain/'

INPUT_PROJECTION = 'EPSG:4326' # (WGS 84)
OUTPUT_PROJECTION = 'EPSG:3857' # (Web Mercator)

lat = 48
lon = 8
 
if False:

    start = time.time()
    result = get_image_(PATH_TO_DATASET, lat, lon, 10)
    end = time.time()
    print(end-start)

    image = result[2]
    box = result[1]
    draw = ImageDraw.Draw(image)
    draw.rectangle(box, outline=255, width=3)
    print(image.size)
    image.show()
    
    
def km_to_pixel(latitude,longitude, km):

    right_longitude = (((longitude+180)+1)%360)-180
    bounds =  (longitude, latitude, right_longitude, latitude+1)
    
    biggest_latitude = lat
    if biggest_latitude > 0:
        biggest_latitude += 1
    
    lat_distance = geopy.distance.geodesic((biggest_latitude,longitude), (latitude,longitude)).km
    lon_distance = geopy.distance.geodesic((biggest_latitude,longitude), (biggest_latitude,right_longitude)).km
    
    lat_radius = km/lat_distance
    lon_radius = km/lon_distance
        
    lats = [biggest_latitude-lat_radius]
    lons = [lon+lon_radius]
    
    transform, width, height = calculate_default_transform(
    INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), 3600, *bounds)
    
    lat_lon = rasterio.warp.transform(INPUT_PROJECTION, OUTPUT_PROJECTION, lons,  lats)
    
    pixel_positions = rasterio.transform.rowcol(transform,lat_lon[0],lat_lon[1])
    
    
    return int((pixel_positions[0] + pixel_positions[1])/2)
    
print('\n')
pixel = km_to_pixel(lat,lon,10)
pixels = [[pixel],[pixel]]
print(pixels)
def pixel_to_coordinates(latitude,longitude, points):

    right_longitude = (((longitude+180)+1)%360)-180
    bounds =  (longitude, latitude, right_longitude, latitude+1)
    
    transform, width, height = calculate_default_transform(
        INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), 3600, *bounds)
    
    y = points[0]
    x = points[1]
    
    mercator_pos = rasterio.transform.xy(transform, x, y, offset='ul')
    
    lat_lon = rasterio.warp.transform(OUTPUT_PROJECTION, INPUT_PROJECTION, [mercator_pos[0]],  [mercator_pos[1]])
    
    return lat_lon

back = pixel_to_coordinates(lat,lon,pixels)
print(back)
print(geopy.distance.geodesic((lat+1,lon), (lat+1,back[0][0])).km)
print(geopy.distance.geodesic((lat+1,lon), (back[1][0],lon)).km)
    
    





