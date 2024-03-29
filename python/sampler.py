from image_loader import get_image
from PIL import Image, ImageDraw
import numpy as np
import os
from utilities import stringify_latitude, stringify_longitude, string_to_position
from utilities import pixel_to_coordinates, km_to_pixel
from halton import halton
import time
import argparse
import random
import math

DEBUG = True

def sample_random_points(latitude, longitude,path_prefix, amount_samples, edge_length, output_dir=None,output_size=None):
        
    #Calculate meters to pixel
    edge_length_pixel = km_to_pixel(latitude,longitude, edge_length)
    
    #TODO cache image
    result = get_image(path_prefix, latitude, longitude, edge_length_pixel)
    if result is None: return None
    
    image, min_height, max_height, placeholders = result
        
    file_prefix = stringify_latitude(latitude) + '_' + stringify_longitude(longitude)
    current_output_dir = os.path.join(output_dir, file_prefix)
    
    if not os.path.exists(current_output_dir): os.makedirs(current_output_dir)
    
    width, height = image.size
    
    content_width = width - 2*edge_length_pixel
    content_height = height -2*edge_length_pixel
    
    radius_pixel = edge_length_pixel * 1.41421356237 #edge_length * sqrt(2)
    
    points = equal_distribution(amount_samples, placeholders, edge_length_pixel, content_width, content_height)
    
    points_lat_lon = pixel_to_coordinates(latitude,longitude, points)
    
    margin = np.array([edge_length_pixel,edge_length_pixel])
    
    #Add Offset
    points_pixel = np.add(points,margin)
    
    for point_id, (x,y) in enumerate(points_pixel):
        file_name = file_prefix+'_'+str(point_id) + ".png"
        
        angle = random.uniform(0, 1)*360.0
    
        with open(os.path.join(output_dir,'labels.csv'), 'a') as file:
            lat, lon  = points_lat_lon[point_id][0], points_lat_lon[point_id][1]
            path = os.path.join(file_prefix,file_name)
            
            csv_line = "{};{};{};{};{};{}\n".format(path,lat,lon,angle,min_height,max_height)
            file.write(csv_line)
    
        point1 = (x - radius_pixel/2,y-radius_pixel/2)
        point2 = (x + radius_pixel/2,y+radius_pixel/2)
        
        image_slice = image.crop((point1[0],point1[1],point2[0],point2[1]))
        image_slice = image_slice.rotate(angle,resample=Image.BICUBIC)
        
        slice_width, slice_height = image_slice.size
        
        margin = int((slice_width-edge_length_pixel)/2)
        
        slice_bounding_box = (margin,margin,slice_width-margin,slice_height-margin)
        
        image_slice = image_slice.crop(slice_bounding_box)
        if output_size is not None: image_slice = image_slice.resize([output_size,output_size],Image.ANTIALIAS)
        
        image_slice.save(os.path.join(current_output_dir,file_name),"PNG")
        
        
    bounding_box = [(edge_length_pixel,edge_length_pixel),(width-edge_length_pixel,height-edge_length_pixel)]
    return image, points_pixel, bounding_box
    

def select_points_with_distance(input_points, distance_points,min_distance):
    
    mask = []
    
    for input_point in input_points:
        min_distance_ok = True
        for distance_point in distance_points:
            distance = math.hypot(distance_point[0] - input_point[0], distance_point[1] - input_point[1])
            if distance < min_distance:
                min_distance_ok= False
                break
        mask.append(min_distance_ok)
        
    return mask
    
    
def equal_distribution(points, placeholders, offset, width, height):
    
    aspect = float(height)/width
        
    halton_size = int(points*0.8)
    random_size = points-halton_size
    
    halton_points = halton(2, halton_size)
    random_points = np.random.rand(random_size, 2)
    
    points = np.concatenate((halton_points,random_points), axis=0)
    
    points = np.multiply(points, np.array([width*aspect,height]).T)
    
    points = points[points[:,0] <= width]
    
    #Pay attention to parts of the image which are filled with placeholders
    
    points_to_keep_distance = []
    
    #Add top offset
    if placeholders[0][1]: points = points[points[:,1] >= offset]
    
    #Add bottom offset
    if placeholders[2][1]: points = points[points[:,1] <= height-offset]
    
    #Add left offset
    if placeholders[1][0]: points = points[points[:,0] >= offset]
    
    #Add right offset
    if placeholders[1][2]: points = points[points[:,0] <= width-offset]
    
    #Upper left
    if not placeholders[0][1] and not placeholders[1][0] and placeholders[0][0]: points_to_keep_distance.append((0,0))
    
    #Upper right
    if not placeholders[0][1] and not placeholders[1][2] and placeholders[0][2]: points_to_keep_distance.append((width,0))
    
    #Lower left
    if not placeholders[2][1] and not placeholders[1][0] and placeholders[2][0]: points_to_keep_distance.append((0,height))
    
    #Lower left
    if not placeholders[2][1] and not placeholders[1][2] and placeholders[2][2]: points_to_keep_distance.append((width,height))
    
    if len(points_to_keep_distance) > 0:
        mask = select_points_with_distance(points, points_to_keep_distance,offset)
        points = points[mask]
    
    return points


def get_patch_list():
    patch_list = []
    for folder in os.listdir(PATH_TO_DATASET):
        if not folder.startswith("."):
            for file in os.listdir(os.path.join(PATH_TO_DATASET,folder)):
                if file.endswith("DSM.tif") and not file.startswith("."):
                    patch_list.append(file)
                    
    return patch_list
    
    
def show_debug_draw(image, points, bounding_box):
    draw = ImageDraw.Draw(image)
    line_color = 255
    
    radius_pixel = 300
            
    for x,y in points:
        point1 = (x - radius_pixel/2,y-radius_pixel/2)
        point2 = (x + radius_pixel/2,y+radius_pixel/2)
        
        draw.ellipse([point1,point2], outline=line_color, width=2)
        
    draw.rectangle(bounding_box, outline=line_color, width=3)
    image.show()
        

def run_sampler(output_size,output_dir,samples_per_patch, sample_edge_length):
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    #Reset labels
    with open(os.path.join(output_dir,'labels.csv'), 'a') as file:
        file.truncate(0)
        file.write('Filename;Latitude;Longitude;Rotation;MinHeight;MaxHeight\n')
        
    all_patches = get_patch_list()
    
    patch_size = len(all_patches)
    
    start = time.time()
    
    for current_patch, patch in enumerate(all_patches):
        lat, lon = string_to_position(patch)
        
        image, points, bounding_box = sample_random_points(lat,lon, amount_samples=samples_per_patch, edge_length=sample_edge_length,output_dir=output_dir, output_size=output_size)
        
        if DEBUG: show_debug_draw(image,points,bounding_box)
            
        end = time.time()
        
        total_time = end - start
        avg_time = total_time/current_patch
        
        output_info = "\n{}/{} - total:{:0.2f}s avg:{:0.2f}s \n".format(current_patch+1, patch_size, total_time,avg_time)
        print(output_info)
    
#run_sampler(output_size=256,output_dir='../samples', samples_per_patch=150, sample_edge_length=10)

# Initiate the parser
parser = argparse.ArgumentParser()

# Add long and short argument
parser.add_argument("input_dir")
parser.add_argument("edge_length",type=float)
parser.add_argument("amount_samples", type=int)
parser.add_argument("--debug", "-d", help="run in debug mode", default=False, type=bool)
parser.add_argument("--size", "-s", help="set the output size", default=None, type=int)
parser.add_argument("--output", "-o", help="set the output directory path", default="../output")

# Read arguments from the command line
args = parser.parse_args()

input_dir = args.input_dir
edge_length = args.edge_length
amount_samples = args.amount_samples

output_dir = args.output
output_size = args.size
DEBUG = args.debug

data = sample_random_points(53, 6, input_dir,amount_samples, edge_length, output_dir=output_dir,output_size=output_size)
if data is not None and DEBUG: show_debug_draw(*data)
else: print("No data")
    
    


