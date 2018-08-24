# Ebola Project Data Analys

## Overview
This package does the following:

 1. Takes a dataset (tested on the etu_1_condensed dataset, not included because it was too long of a directory) and reduces it down to a skeleton

2. Places nodes where each "highway" (a skeletonized segment) begins and ends

3. Finds the ways that all of the nodes are connected (essentially makes a graph map)

4. Makes a lookup table to find what the node closest to each pixel is

5. Makes a gif of the flood fill used in (4)

6. Slices all of the paths that the robot took and turns that into data of how long the robot took to traverse each highway

7. Makes histograms of the distributions of times for each path

In order to run the code in its full form, use the file [make_data.sh](make_data.sh)

## Skeletonization
The first script that runs is [cluster_and_skel2.py](cluster_and_skel2.py). This first extracts the data from the pickles in etU_1_condensed and turns that into a heatmap of where the robot traveled. The resolution is .05 meters per pixel as defined in [map.yaml](map.yaml). From here, it uses an image processing technique to get the skeletonization.

First, it does a thresholding process with a threshold of 0 so that any place where the robot was can be picked up by the skeletonization, which only takes bitmaps. Then it skeletonizes, reducing any regions to 1px wide. Unfortunately this leads to a lot of extra lines spider-webbing out of the main paths, so the whole skeleton gets blurred, thresholded at 90% to get rid of the least dense areas, and re-skeletonized, which produces a [much cleaner skeleton](cont_skel_2.png)

It saves the output skeleton as mask_data.npy

NB: This is called cluster and skel(etonize), but it turns out that the clustering didn't make any difference. For old code, see the [ebola_project repo](https://github.com/sagekg/ebola-project)

## Node Placement
[node_place.py](node_place.py) runs through all of the pixels in mask_data.npy and looks for any point which has a number of neighbors != 2. If there is only 1, it's a terminal node. If there are 3, then it's where highways split. It saves a list of all of the points in the skeleton (skel_pts.npy) and also a list of the locations of each node and the number of connections for each node (node_pts.npy)
## Graph Generation
[generate_graph.py](generate_graph.py) has a lot of logic in it, and for that you should look at the comments in the code. In general, though, this script looks at how the nodes are connected to each other and does the following:

1. Removes nodes that are only connected to each other, as those are just unconnected segments

2. Removes nodes that have only one connection and have a short connection path (15px), as those are just extra ones off to the side

3. Removes sets of nodes that are clustered together (within 3px). This happens when highways intersect and there are a number of nodes that are describing the same intersection

4. Removes any self connections that appear due to this process

5. Removes spots where stub paths were connected to clusters that only are apparent after the previous steps

6. Looks back through the connections and redoes the list such that node connections match with the indices. This probably could/should have been done with a class & hash setup, but I really don't understand hashes that well so this works

## Voronoi Expansion/Flood Fill
[voronoi_expansion.py](voronoi_expansion.py) is a simple flood fill algorithm that floods from each node and continues in every direction until it hits a wall or another node zone

## Gif Making
[make_gif.py](make_gif.py) takes images that are saved out of voronoi_expansion.py and writes them into a gif. For later purposes it'd probably be a good idea to comment out the image saving from the voronoi expansion and also this script entirely.

## Path Slicing
[pathfinder8.py](pathfinder8.py) is intended to find how long the robot spent on any given highway. It does this by:

1. For each path, interpolating a number of points in between each actual data point so we can get a better resolution

2. Finding what node zone each point is in, and calculating the distance from that node and the time in the path.

3. Looking at the distances in each node zone and finding the minimum, and then finding the time between minimums

4. For each time between between two nodes, it appends that time to a list of times for the path between any two given nodes

It saves out the final data as a square matrix where the first index is the starting node and the second is the ending node. The information in between is a list of the times it spent in between those nodes. This data does not take into account whether or not the nodes have a highway connection or not. It is saved in the file time_data.npy.

## Histogram
[histogram.py](histogram.py) outputs a histogram for each path that has a valid highway connection.

## Requirements
This code was tested on Python 3.5.2. It uses the following packages:

* numpy 1.15.0
* matplotlib 2.2.2
* scipy 0.17.0
* scikit-image (skimage) 0.14.0
* scikit-learn (sklearn) 0.19.2
* Python Image Library (PIL) 1.1.7
* yaml 3.11
* re 2.2.1
* imageio 2.3.0
* tqdm 4.24.0
* animation 0.0.5
