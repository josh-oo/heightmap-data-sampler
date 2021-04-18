import time
from PIL import ImageDraw, Image
import os

from process_images import get_image
from process_images_ import get_image_, get_file_paths

import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np

PATH_TO_DATASET = '/Volumes/Extreme SSD/Datasets/Terrain/'

lat = 59
lon = 8

COMPARE = False

if COMPARE:
    start = time.time()
    result = get_image(PATH_TO_DATASET, lat, lon, 10)
    end = time.time()
    print(end-start)

    image = result[2]
    box = result[1]
    draw = ImageDraw.Draw(image)
    draw.rectangle(box, outline=255, width=3)
    print(image.size)
    image.show()
    
    image.save("old.png","PNG")

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
    

with rasterio.open(src_path) as src:
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds)
        

    destination = np.zeros((height,width), np.float32)

    reproject(
        source=rasterio.band(src, 1),
        destination=destination,#rasterio.band(dst, i),
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform,
        dst_crs=dst_crs,
        resampling=Resampling.nearest)
        
max_height = np.max(destination)
min_height = np.min(destination)

destination = (destination - min_height) / (max_height-min_height)

image = Image.fromarray(np.uint8(destination * 255), 'L')
image.show()
image.save(dst_path,"PNG")
