#!/usr/bin/env python3

#General Packages
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

#Packages to make life easier
import os
from tqdm import tqdm, trange
from PIL import Image
import yaml, glob, pickle

def euclidean(pt, node):
    return np.sqrt((pt[0]-node[0])*(pt[0]-node[0]) + (pt[1]-node[1])*(pt[1]-node[1]))

def interpolate_data(last_pt, pt, res, origin, num_pts):
    last_x = last_pt.position.x - origin[0]
    last_y = last_pt.position.y - origin[1]
    last_x_coord = int(last_x/res)
    last_y_coord = im_h - int(last_y/res)

    x = pt.position.x - origin[0]
    y = pt.position.y - origin[1]
    x_coord = int(x/res)
    y_coord = im_h - int(y/res)

    x = np.linspace(last_x_coord, x_coord, num_pts)
    if x_coord-last_x_coord != 0:
        m = -(y_coord - last_y_coord)/(x_coord - last_x_coord)
    else:
        return [(x_coord, y_coord)]*num_pts
    y = -np.subtract(m*np.subtract(x, last_x_coord), last_y_coord).astype(int)

    return list(zip(x.astype(int), y))

def show_path(pts, lastnode, node, mask, node_pts):
    fig = plt.figure()
    plt.ylim(2300, 1790)
    plt.xlim(1620, 2300)
    implot = plt.imshow(mask, cmap=plt.cm.nipy_spectral, Animated=True)

    for pt in pts:
        plt.scatter(pt[0], pt[1], c='b', marker='.')

    plt.scatter(node_pts[node][1],node_pts[node][0], c='g')
    plt.scatter(node_pts[lastnode][1],node_pts[lastnode][0], c='g')

plt.show()

class Pt:
    def __init__(self, dist, time, deriv, id, parent):
        self.s = dist
        self.t = time
        self.v = deriv
        self.id = id
        self.parent = parent

if __name__ == "__main__":
    path = os.getcwd() + '/'
    data_path = path + 'etu_1_condensed/'#courtyard_0_bed_0.p'
    # data_path = path + 'etu_1_condensed/test/'

    step = 1
    num_pts = 10

    node_pts = np.load(path + 'node_data.npy')[:,0].tolist()
    voronoi_mask = np.load(path + 'voronoi_expansion_mask.npy')
    node_cons = np.load(path + 'node_data.npy')[:,1]

    poses = yaml.load(open(path + 'amcl_poses.yaml', 'rb'))
    map_params = yaml.load(open(path + 'map.yaml', 'rb'))
    origin = map_params['origin']
    res = map_params['resolution'] #meters per pixel
    I = Image.open(path + 'map.pgm')
    imarray = np.asarray(I).astype('int')
    w, h = I.size
    im_w = int(w/step)
    im_h = int(h/step)

    files = glob.glob(data_path + '*.p')

    #generate matrix for data
    data_mtx = [[[] for k in range(len(node_pts))] for i in range(len(node_pts))]

    #tqdm.write("Getting path data")
    for file in tqdm(files, position = 0):
        dataset = pickle.load(open(file, 'rb'))

        if dataset == []:
            continue

        for trial in dataset:
            if trial[1] > 1000 or trial[0] == 4:
                # #tqdm.write("bad trial " + str(file))
                continue

            #Generate num_pts in between each pair of points in a given trial
            interpolated_data = []
            for i, point in enumerate(trial[2]):
                x = point.position.x - origin[0]
                y = point.position.y - origin[1]
                x_coord = int(x/res)
                y_coord = im_h - int(y/res)

                if i == 0:
                    interpolated_data.append((x_coord, y_coord))
                    continue
                interpolated_data.extend(interpolate_data(trial[2][i-1], point, res, origin, num_pts))

            #Test to make sure that the path actually goes somewhere, otherwise we can skip it
            if (voronoi_mask[interpolated_data[0][1]][interpolated_data[0][0]] ==
                voronoi_mask[interpolated_data[-1][1]][interpolated_data[-1][0]]):
                continue

            # fig = plt.figure()
            # plt.ylim(2300, 1790)
            # plt.xlim(1620, 2300)
            # implot = plt.imshow(voronoi_mask, cmap=plt.cm.nipy_spectral, Animated=True)

            #Get points
            time = 0
            data = []
            for point in interpolated_data:
                node_id = voronoi_mask[point[1]][point[0]] #voronoi_mask is flipped
                dist = euclidean(point, node_pts[node_id])
                if data:
                    deriv = dist - data[-1].s
                    data.append(Pt(dist, time, deriv, node_id))
                else:
                    data.append(Pt(dist, time, None, node_id))
                time += 1

            last_point = None
            inflection_pts = []
            for point in data:
                if last_point != None:
                    if point.v > 0 and last_point.v <= 0:
                        if last
                        inflection_pts.append(point)
