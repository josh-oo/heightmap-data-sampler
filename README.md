# Heightmap Data Sampler
Some scripts to sample quadratic patches from given real-world heightmap data.  
Data source: https://www.eorc.jaxa.jp/ALOS/en/aw3d30/index.htm

## Get Started
Download the GeoTIFFs of your target area from the source above and place the folders in a root directory (In this case /SSD/Datasets/Terrain/ ).
Execute the RunSampler script and put this root directory to the first argument to get equal-sized sample patches.

## Documentation
./RunSampler *ROOT_DIRECTORY_OF_ALOS_DATA* *DESIRED_PATCH_SIZE_IN_KM* *NUMBER_OF_SAMPLES_PER_PATCH*

### Options
-o: Output directory   
-s: Size of output patches in pixels  
-d: Enable debug mode  

## Example
./RunSampler /SSD/Datasets/Terrain/ 10 150 -o ../output -s 256 -d  
Result: 150 patches of real world size of 10x10km and pixel size 256x256 for each GeoTIFF in /SSD/Datasets/Terrain/
