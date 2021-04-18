import time
from PIL import ImageDraw, Image
import os

from process_images import get_image, get_file_paths, get_pixel_width

import rasterio
from rasterio.warp import calculate_default_transform, reproject,transform_bounds, Resampling
import numpy as np

PATH_TO_DATASET = '/Volumes/Extreme SSD/Datasets/Terrain/'

INPUT_PROJECTION = 'EPSG:4326' # (WGS 84)
OUTPUT_PROJECTION = 'EPSG:3857' # (Web Mercator)

lat = 59
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

dst_crs = 'EPSG:3857'#'EPSG:4326'

file_name, folder_name = get_file_paths(lat,lon)
src_path = os.path.join(PATH_TO_DATASET, folder_name, file_name)
dst_path = '/Users/joshua/Desktop/' + file_name +'_Projected.png'

#image.save(dst_path.replace('_','_1_'),"PNG")
    

def get_pixel_transformed(latitude,longitude, points):

    right_longitude = (((longitude+180)+1)%360)-180
    bounds = (longitude, latitude, right_longitude, latitude+1)
    
    transform, width, height = calculate_default_transform(
        INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), 3600, *bounds)
    
    x = points[:,0]
    y = points[:,1]
    
    mercator_pos = rasterio.transform.xy(transform, x, y, offset='ul')
    
    lat_lon = rasterio.warp.transform(OUTPUT_PROJECTION, INPUT_PROJECTION, mercator_pos[0],  mercator_pos[1])
    
    return np.stack(lat_lon, axis = 1)
    
width = 2304
height = 4540
#bounds, first_transform,transform = get_pixel_transform(lat,lon,width=width,height=height)
#print(transform)
x = height
y = width#factor

# 0 -> 8
# 0 -> 60

# ? -> 9
# ? -> 59

input = np.array([[x,y],[x*0.5,y*0.5],[x*0.1,y*0.1]])

print(get_pixel_transformed(lat,lon,input))
#result = rasterio.transform.xy(first_transform, [x], [y], offset='ul')
#print(result)
#print(rasterio.warp.transform(OUTPUT_PROJECTION, INPUT_PROJECTION, [result[0]], [result[1]]))
#print(rasterio.transform.xy(transform, [x], [y], offset='center'))




