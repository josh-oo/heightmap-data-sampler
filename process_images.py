from PIL import Image
import numpy as np
import os
from utilities import stringify_latitude, stringify_longitude, get_patch_dimensions

import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

#Image metadata
IMAGE_HEIGHT = 3600
#IMAGE_WIDTH = 'VARIABLE'
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
    
def get_target_pixel_dimensions(latitude,longitude):
    right_longitude = (((longitude+180)+1)%360)-180
    bounds = (longitude, latitude, right_longitude, latitude+1)
    transform, width, height = calculate_default_transform(
        INPUT_PROJECTION, OUTPUT_PROJECTION, get_pixel_width(latitude), IMAGE_HEIGHT, *bounds)
        
    return width, height

def get_neighbours(latitude, longitude):
    
    neighbour_list = [(None,None)]*9
    
    left_longitude = (((longitude+180)-1)%360)-180
    right_longitude = (((longitude+180)+1)%360)-180
    
    #Left
    pos = (latitude,  left_longitude)
    neighbour_list[3] = pos
    
    #Original
    pos = (latitude,  longitude)
    neighbour_list[4] = pos
    
    #Right
    pos = (latitude,  right_longitude)
    neighbour_list[5] = pos
    
    #Top
    if latitude + 1 <= 90:
        top_latitude = latitude + 1
        
        pos = (top_latitude, longitude)
        neighbour_list[1] = pos
        
        pos = (top_latitude, left_longitude)
        neighbour_list[0] = pos
        
        pos = (top_latitude, right_longitude)
        neighbour_list[2] = pos
    
    #Bottom
    if latitude - 1 >= -90:
        bottom_latitude = latitude - 1
        
        pos = (bottom_latitude, longitude)
        neighbour_list[7] = pos
        
        pos = (bottom_latitude, left_longitude)
        neighbour_list[6] = pos
        
        pos = (bottom_latitude, right_longitude)
        neighbour_list[8] = pos
    
        
    return neighbour_list
    
    
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
    
def get_placeholder(latitude,target_width):
    actual_width = get_pixel_width(latitude)
    scale_factor = float(target_width) / float(actual_width)
    scaled_width = int(actual_width*scale_factor)
    scaled_height = int(3600*scale_factor)

    #swap width and height to match pillow
    return np.zeros((scaled_height,scaled_width))
    
def get_mercator_projected_image(path):
    with rasterio.open(path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, OUTPUT_PROJECTION, src.width, src.height, *src.bounds)

        destination = np.zeros((height,width), np.float32)

        reproject(
            source=rasterio.band(src, 1),
            destination=destination,#rasterio.band(dst, i),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=OUTPUT_PROJECTION,
            resampling=Resampling.nearest)

    return destination
    
def get_current_image(path, tile_pos, edge_length,patch_dimensions, latitude, longitude):

    if tile_pos == (1,1):
        image = get_mercator_projected_image(path)
        return image
        
    target_width, target_height = get_target_pixel_dimensions(latitude,longitude)
    
    top_bottom_height = int((edge_length/patch_dimensions[0])*target_height)
    top_bottom_width = target_width
    
    left_right_height = target_height
    left_right_width = int((edge_length/patch_dimensions[1])*target_width)
    
    use_placeholder = not os.path.exists(path)
    
    current_width = 0
    current_height = 0
    
    crop_top = 0
    crop_bottom = target_height
    crop_left = 0
    crop_right = target_width
    

    if tile_pos[1] == 0 or tile_pos[1] == 2:
        current_height = top_bottom_height
        
        if tile_pos[1] == 0:
            #Top
            crop_top = crop_bottom - current_height
        
        if tile_pos[1] == 2:
            #Bottom
            crop_bottom = current_height
        
        if tile_pos[0] == 0:
            #Left
            current_width = left_right_width
            crop_left = crop_right - current_width
            
        if tile_pos[0] == 2:
            #Right
            current_width = left_right_width
            crop_right = current_width
            
        if tile_pos[0] == 1:
            #Center
            current_width = target_width
    
    if tile_pos[1] == 1:
        current_width = left_right_width
        current_height = left_right_height
        
        if tile_pos[0] == 0:
            #Left
            crop_left = crop_right - current_width
            
        if tile_pos[0] == 2:
            #Right
            crop_right = current_width
        
    if use_placeholder == False:
        print(path)
        image_array = get_mercator_projected_image(path)

        cropped = image_array[crop_top:crop_bottom, crop_left:crop_right]
        return cropped
        
    else:
        print('Load Placeholder')
        return np.zeros((current_height,current_width))
        
        
def get_row(path_to_dataset,row,radius,patch_dimensions, patches):
    
    image_row = None

    for i in range (len(patches)):
        lat, lon = patches[i]

        file_name,folder_name = get_file_paths(lat,lon)

        path = os.path.join(path_to_dataset, folder_name, file_name)
        
        image  = get_current_image(path, (i, row), radius, patch_dimensions, lat, lon)
            
    
        if image_row is None:
            image_row = image
        else:
            image_row = np.concatenate((image_row, image), axis = 1)
            
    return image_row
    
def scale_row(row, target_width=None):

    row_image = Image.fromarray(np.uint8(row * 255), 'L')
    width, height = row_image.size

    if target_width is not None:
        factor = float(target_width)/width
        width = target_width
        height = int(factor*height)
    
    scaled_image = row_image.resize([width,height],Image.ANTIALIAS)
    return scaled_image
    
    
def get_image(path_to_dataset, latitude,longitude, radius=10):

    file_name, folder_name = get_file_paths(latitude,longitude)
    path = os.path.join(path_to_dataset, folder_name, file_name)
    
    if not os.path.exists(path):
        return None

    print('\nProcess ' + file_name)
    patch_list = get_neighbours(latitude,longitude)
    
    patch_dimensions = get_patch_dimensions(latitude)

    col = 0
    row = 0

    current_row = None
    rows = None

    target_width, target_height = get_target_pixel_dimensions(latitude,longitude)
    
    top_latitude = patch_list[0][0]
    middle_latitude = patch_list[3][0]
    bottom_latitude = patch_list[6][0]

    #Get rows
    middle_row = get_row(path_to_dataset,1,radius,patch_dimensions,[patch_list[3],patch_list[4],patch_list[5]])
    top_row = get_row(path_to_dataset,0,radius,patch_dimensions,[patch_list[0],patch_list[1],patch_list[2]])
    bottom_row = get_row(path_to_dataset,2,radius,patch_dimensions,[patch_list[6],patch_list[7],patch_list[8]])
    
    #Normalize images
    max_height = np.max([np.max(middle_row),np.max(top_row),np.max(bottom_row)])
    min_height = np.min([np.min(middle_row),np.min(top_row),np.min(bottom_row)])
    
    middle_row = (middle_row - min_height) / (max_height-min_height)
    top_row = (top_row - min_height) / (max_height-min_height)
    bottom_row = (bottom_row - min_height) / (max_height-min_height)
    
    #Mercator projection
    middle_row_image = scale_row(middle_row)
    top_row_image = scale_row(top_row,target_width=middle_row_image.size[0])
    bottom_row_image = scale_row(bottom_row,target_width=middle_row_image.size[0])
    
    top_margin = top_row_image.size[1]
    bottom_margin = bottom_row_image.size[1]
    
    image_height = middle_row_image.size[1]
    
    new_image = Image.new('L', (middle_row.shape[1], top_margin+image_height+bottom_margin), 0)
    
    new_image.paste(top_row_image, (0, 0))
    new_image.paste(middle_row_image, (0, top_margin))
    new_image.paste(bottom_row_image, (0, top_margin + image_height))

    width, height = new_image.size


    longitude_distance_in_km = patch_dimensions[1]
    latitude_distance_in_km = patch_dimensions[0]
    
    radius_latitude = radius / latitude_distance_in_km
    radius_longitude = radius / longitude_distance_in_km

    horizontal_margin = int((width-target_width)/2)
    
    content_bounding_box = [(horizontal_margin,top_margin),(width-horizontal_margin,height-bottom_margin)]
    
    
    return radius_latitude, content_bounding_box, new_image
