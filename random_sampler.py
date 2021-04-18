from process_images import get_image
from PIL import Image, ImageDraw
import numpy as np
from math import sqrt
import random
import os
from utilities import stringify_latitude, stringify_longitude, get_patch_dimensions, string_to_position
from uniform_density import Field, halton
import time

PATH_TO_DATASET = '/Volumes/Extreme SSD/Datasets/Terrain/'
DEBUG = False

def sample_random_points(latitude, longitude, amount_samples, edge_length, output_dir=None,output_size=None):
    
    #TODO cache image
    result = get_image(PATH_TO_DATASET, latitude, longitude, edge_length)
    if result is None:
        return
        
    file_prefix = stringify_latitude(latitude) + '_' + stringify_longitude(longitude)
        
    current_output_dir = os.path.join(output_dir, file_prefix)
    
    if not os.path.exists(current_output_dir):
        os.makedirs(current_output_dir)
    
        
    new_image = result[2]
    bounding_box = result[1]
    edge_length_latitude = result[0]
    
    width, height = new_image.size
    
    content_width = bounding_box[1][0] - bounding_box[0][0]
    content_height = bounding_box[1][1] - bounding_box[0][1]

    draw = ImageDraw.Draw(new_image)
    line_color = 255
    
    edge_length_pixel = edge_length_latitude * content_height
    radius_pixel = edge_length_pixel * 1.41421356237 #edge_length * sqrt(2)
    
    points = equal_distribution(latitude, amount_samples)
    
    
    point_id = 0
    for x,y in points:
    
        file_name = file_prefix+'_'+str(point_id) + ".png"
    
        with open(os.path.join(output_dir,'labels.csv'), 'a') as file:
            current_lat = str(latitude + x)
            current_lon = str(longitude + y)
            file.write(file_name + ';'+current_lat+';'+ current_lon+'\n')
    
        point1 = (x*content_width - radius_pixel/2,y*content_height-radius_pixel/2)
        point2 = (x*content_width + radius_pixel/2,y*content_height+radius_pixel/2)
        
        margin = (bounding_box[0][0],bounding_box[0][1])
        
        point1 = tuple(map(lambda x, y: x + y, point1, margin))
        point2 = tuple(map(lambda x, y: x + y, point2, margin))
        
        angle = random.uniform(0, 1)*360.0
        
        image_slice = new_image.crop((point1[0],point1[1],point2[0],point2[1]))
        image_slice = image_slice.rotate(angle,resample=Image.BICUBIC)
        
        slice_width, slice_height = image_slice.size
        
        margin = int((slice_width-edge_length_pixel)/2)
        
        slice_bounding_box = (margin,margin,slice_width-margin,slice_height-margin)
        
        image_slice = image_slice.crop(slice_bounding_box)
        if output_size is not None:
            image_slice = image_slice.resize([output_size,output_size],Image.ANTIALIAS)
        
        image_slice.save(os.path.join(current_output_dir,file_name),"PNG")
        point_id += 1
        
        if DEBUG:
            draw.ellipse([point1,point2], outline=line_color, width=2)
      
    if DEBUG:
        draw.rectangle(bounding_box, outline=line_color, width=3)
        new_image.show()
        new_image.save("merged_image.png","PNG")
    
def equal_distribution(latitude, points):

    #TODO Improve this sample method
    assert points > 10
    
    halton_size = int(points*0.8)
    random_size = points-halton_size
    
    halton_points = halton(2, halton_size)
    random_points = np.random.rand(random_size, 2)
    
    points = np.concatenate((halton_points,random_points), axis=0)
    
    #slice sample points
    lat, lon = get_patch_dimensions(latitude)
    
    aspect = lat/lon
    
    scale = np.array([aspect,1.0])
    points = np.multiply(points,scale.T)
    
    points = points[points[:,0] <= 1.0]
    
    
    return points

    
def get_patch_list():
    patch_list = []
    for folder in os.listdir(PATH_TO_DATASET):
        if not folder.startswith("."):
            for file in os.listdir(os.path.join(PATH_TO_DATASET,folder)):
                if file.endswith("DSM.tif") and not file.startswith("."):
                    patch_list.append(file)
                    
    return patch_list

def run_sampler(output_size,output_dir,samples_per_patch, sample_edge_length):
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    #Reset labels
    with open(os.path.join(output_dir,'labels.csv'), 'a') as file:
        file.truncate(0)
        file.write('Filename;Latitude;Longitude\n')
        
    all_patches = get_patch_list()
    
    patch_size = len(all_patches)
    current_patch = 1
    
    start = time.time()
    
    for patch in all_patches:
        lat, lon = string_to_position(patch)
        
        sample_random_points(lat,lon, amount_samples=samples_per_patch, edge_length=sample_edge_length,output_dir=output_dir, output_size=output_size)
        
        end = time.time()
        
        avg_time = (end - start)/current_patch
        
        print('\n' + str(current_patch) + '/' + str(patch_size) + ' - ' + str(int(end - start))+ 's '+ 'avg: '+ str(avg_time)+ 's \n')
        
        current_patch += 1
    
run_sampler(output_size=256,output_dir='../samples', samples_per_patch=150, sample_edge_length=10)
    
    


