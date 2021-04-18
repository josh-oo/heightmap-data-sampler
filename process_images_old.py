from PIL import Image
import numpy as np
import os
from utilities import stringify_latitude, stringify_longitude, calculate_distance

def get_pixel_width(latitude):
    #Specs from https://www.eorc.jaxa.jp/ALOS/en/aw3d30/aw3d30v3.2_product_e_e1.2.pdf
    if latitude >= 80 or latitude <= -80:
        return 600
    if latitude >= 70 or latitude <= -70:
        return 1200
    if latitude >= 60 or latitude <= -60:
        return 1800
    #default
    return 3600

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

def get_image(path_to_dataset, latitude,longitude, radius=10):

    file_name, folder_name = get_file_paths(latitude,longitude)
    path = os.path.join(path_to_dataset, folder_name, file_name)
    if not os.path.exists(path):
        return None

    print('\nProcess ' + file_name)
    patch_list = get_neighbours(latitude,longitude)

    col = 0

    current_row = None
    rows = None

    target_width = get_pixel_width(latitude)

    horizontal_guidelines = []

    for lat,lon in patch_list:

        file_name,folder_name = get_file_paths(lat,lon)

        path = os.path.join(path_to_dataset, folder_name, file_name)
        
        if not os.path.exists(path):
            print('Load Placeholder')
            image = get_placeholder(lat, target_width)
        else:
            print('Load ' + file_name)
            image = Image.open(path)
            width, height = image.size

            scale_factor = float(target_width) / float(width)
            
            image = image.resize([int(width*scale_factor),int(height*scale_factor)],Image.ANTIALIAS)
            
            image = np.asarray(image).astype('float')
            
    
        if current_row is None:
            current_row = image
        else:
            current_row = np.concatenate((current_row, image), axis = 1)
            
        col += 1
        if col > 2:
            col = 0
            if rows is None:
                rows = current_row
            else:
                rows = np.concatenate((rows, current_row), axis = 0)
            horizontal_guidelines.append(current_row.shape[0])
            current_row = None
          
    image_array = rows

    max_height = float(np.max(image_array))
    min_height = float(np.min(image_array))

    normalized_image_array = (image_array - min_height) / (max_height-min_height)

    new_image = Image.fromarray(np.uint8(normalized_image_array * 255), 'L')
    width, height = new_image.size
    
    x1 = 1/3
    x2 = 2/3
    
    y1 = (horizontal_guidelines[0]) / height
    y2 = (horizontal_guidelines[0]+horizontal_guidelines[1]) / height
    
    #Mercator projection stuff
    longitude_distance_in_km = calculate_distance(patch_list[4],patch_list[5])
    latitude_distance_in_km = calculate_distance(patch_list[4],patch_list[1])
    
    #Crop image
    radius_latitude = radius / latitude_distance_in_km
    radius_longitude = radius / longitude_distance_in_km
    radius_screen_space_lat = radius_latitude*(y2-y1)
    radius_screen_space_lon = radius_longitude*(y2-y1)
    
    crop_bounding_box = ((x1-radius_screen_space_lon)*width,(y1-radius_screen_space_lat)*height,
    (x2+radius_screen_space_lon)*width,(y2+radius_screen_space_lat)*height)
    
    new_image = new_image.crop(crop_bounding_box)
    
    #Stretch image
    vertical_scale_factor = (latitude_distance_in_km/3600) / (longitude_distance_in_km/target_width)
    print(vertical_scale_factor)
    
    new_image = new_image.resize([width,int(height*vertical_scale_factor)],Image.ANTIALIAS)
    width, height = new_image.size

    #TODO consider empty image margins
    vertical_margin = (radius_latitude/(radius_latitude*2.0+1.0))*height
    horizontal_margin = (radius_longitude/(radius_longitude*2.0+1.0))*width
    
    content_bounding_box = [(horizontal_margin,vertical_margin),(width-horizontal_margin,height-vertical_margin)]
    
    
    return radius_latitude, content_bounding_box, new_image
