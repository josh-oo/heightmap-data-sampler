from PIL import Image
import numpy as np
import os
import utilities
from utilities import get_file_paths, get_pixel_width, get_target_pixel_dimensions


import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
    
def get_neighbours(latitude, longitude):
    
    left_longitude = (((longitude+180)-1)%360)-180
    right_longitude = (((longitude+180)+1)%360)-180
    
    lats, lons = [None,latitude,None],[left_longitude,longitude,right_longitude]
    
    #Top
    if latitude + 1 <= 90: lats[0] = latitude + 1
    
    #Bottom
    if latitude - 1 >= -90: lats[2] = latitude - 1
    
    return lats, lons
    
def get_placeholder(latitude,target_width):
    actual_width = get_pixel_width(latitude)
    scale_factor = float(target_width) / float(actual_width)
    scaled_width = int(actual_width*scale_factor)
    scaled_height = int(utilities.IMAGE_HEIGHT*scale_factor)

    #swap width and height to match pillow
    return np.zeros((scaled_height,scaled_width))
    
def get_mercator_projected_image(path):
    with rasterio.open(path) as src:
        transform, width, height = calculate_default_transform(
            src.crs, utilities.OUTPUT_PROJECTION, src.width, src.height, *src.bounds)

        destination = np.zeros((height,width), np.float32)

        reproject(
            source=rasterio.band(src, 1),
            destination=destination,#rasterio.band(dst, i),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=utilities.OUTPUT_PROJECTION,
            resampling=Resampling.nearest)

    return destination
    
def get_current_image(path, tile_pos, offset, width, height):

    if tile_pos == (1,1): return get_mercator_projected_image(path), False
        
    
    top_bottom_height = offset
    top_bottom_width = width
    
    left_right_height = height
    left_right_width = offset
    
    use_placeholder = not os.path.exists(path)
    
    current_width = 0
    current_height = 0
    
    crop_top = 0
    crop_bottom = height
    crop_left = 0
    crop_right = width
    

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
            current_width = width
    
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
        return cropped, False
        
    else:
        print('Load Placeholder')
        return np.zeros((current_height,current_width)), True
        
        
def get_row(path_to_dataset,row,offset,target_width, lons, lat):
    
    image_row = None
    
    row_width, row_height = get_target_pixel_dimensions(lat,lons[0])
    
    offset = int(offset*float(row_width)/target_width)
    
    placholders = [True,True,True]

    for col, lon in enumerate(lons):

        file_name,folder_name = get_file_paths(lat,lon)

        path = os.path.join(path_to_dataset, folder_name, file_name)
        
        image, is_placeholder  = get_current_image(path, (col, row), offset, row_width, row_height)
        placholders[col] = is_placeholder
    
        if image_row is None: image_row = image
        else: image_row = np.concatenate((image_row, image), axis = 1)
            
    return image_row, placholders
    
def scale_row(row, target_width=None):

    row_image = Image.fromarray(np.uint8(row * 255), 'L')
    width, height = row_image.size

    if target_width is not None:
        factor = float(target_width)/width
        width = target_width
        height = int(factor*height)
    
    scaled_image = row_image.resize([width,height],Image.ANTIALIAS)
    return scaled_image
    
    
def get_image(path_to_dataset, latitude,longitude, offset=0):

    file_name, folder_name = get_file_paths(latitude,longitude)
    path = os.path.join(path_to_dataset, folder_name, file_name)
    
    if not os.path.exists(path): return None

    print('\nProcess ' + file_name)
    lats,lons = get_neighbours(latitude,longitude)

    target_width, target_height = get_target_pixel_dimensions(latitude,longitude)

    #Get rows
    middle_row, middle_placeholders = get_row(path_to_dataset,1,offset,target_width,lons,lats[1])
    top_row, top_placeholders = get_row(path_to_dataset,0,offset,target_width,lons,lats[0])
    bottom_row, bottom_placeholders = get_row(path_to_dataset,2,offset,target_width,lons,lats[2])
    
    #Normalize images
    max_height = np.max([np.max(middle_row),np.max(top_row),np.max(bottom_row)])
    min_height = np.min([np.min(middle_row),np.min(top_row),np.min(bottom_row)])
    
    middle_row = (middle_row - min_height) / (max_height-min_height)
    top_row = (top_row - min_height) / (max_height-min_height)
    bottom_row = (bottom_row - min_height) / (max_height-min_height)
    
    #Scale patches
    middle_row_image = scale_row(middle_row)
    top_row_image = scale_row(top_row,target_width=middle_row_image.size[0])
    bottom_row_image = scale_row(bottom_row,target_width=middle_row_image.size[0])
    
    top_margin = top_row_image.size[1]
    bottom_margin = bottom_row_image.size[1]
    
    image_height = middle_row_image.size[1]
    
    image = Image.new('L', (middle_row.shape[1], top_margin+image_height+bottom_margin), 0)
    
    image.paste(top_row_image, (0, 0))
    image.paste(middle_row_image, (0, top_margin))
    image.paste(bottom_row_image, (0, top_margin + image_height))

    placeholders = [top_placeholders,middle_placeholders,bottom_placeholders]

    return image, min_height, max_height, placeholders
