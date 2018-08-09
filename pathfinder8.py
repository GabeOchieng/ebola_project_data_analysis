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
        #If this moves laterally, we can make a slope and generate y data
        m = -(y_coord - last_y_coord)/(x_coord - last_x_coord)
    else:
        if y_coord-last_y_coord == 0:
            #If there is no delta x and no delta y, this is just all one point
            return [(x_coord, y_coord)]*num_pts
        else:
            #Otherwise this is a vertical line, so we need to interpolate
            #   between the y points
            y = np.linspace(last_y_coord, y_coord, num_pts)
            return list(zip(x.astype(int), y.astype(int)))
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

def inflection_check(point, cur_depth):
    #inflection_check returns true if the last nonzero v is
    #   < 0, and false if > 0
    # tqdm.write("inflection_check")
    cur_depth += 1
    # tqdm.write(str(point.v))
    if cur_depth > 600:
        tqdm.write("stuck")
        return False

    if point.v < 0:
        #The original point will have v > 0, so if we have a negative v
        #   that means we have an inflection
        # tqdm.write("True")
        # plt.waitforbuttonpress()
        return True
    elif point.v == 0 and point.parent != None:
        #If the parent is zero, we need to keep searching back in the list.
        #   We also need to make sure we don't pass the beginning of the list
        # tqdm.write("maybe")
        # tqdm.write(str(point.parent))
        return inflection_check(point.parent, cur_depth)
    else:
        #This means we found a positive value or hit the edge of the zone
        #   so this is not an inflection point
        # tqdm.write("False")
        # plt.waitforbuttonpress()
        return False

def check_beginning(point, zone, cut_pts, cur_depth):
    #This function works its way backwards looking for previously found cut points
    if cur_depth > 600:
        tqdm.write("slow start")
        return False
    cur_depth += 1
    if point in cut_pts or point.s > 20:
        return False
    if point.parent == None:
        return True
    return check_beginning(point.parent, zone, cut_pts, cur_depth)

def zone_path(pt, reg_zone_path):
    if pt.id not in reg_zone_path:
        reg_zone_path.append(pt.id)
    return reg_zone_path

# class Pt:
#     def __init__(self, dist, time, deriv, id, parent):
#         self.s = dist
#         self.t = time
#         self.v = deriv
#         self.id = id
#         self.parent = parent

class Pt:
    def __init__(self, dist, time, id):
        self.s = dist
        self.t = time
        self.id = id

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


            #Get points
            time = 0
            data = []
            node_id_list = []
            zone_path = []
            for point in interpolated_data:
                node_id = voronoi_mask[point[1]][point[0]] #voronoi_mask is flipped
                dist = euclidean(point, (node_pts[node_id][1], node_pts[node_id][0]))
                # node_id_list.append(node_id)
                if not zone_path or node_id != zone_path[-1]:
                    zone_path.append(node_id)
                data.append(Pt(dist, time, node_id))
                time+=1

            #Get rid of short moves into other zones
            elided_data = []
            elided_zone_path = []
            for zone in zone_path:
                #Get all points in a given zone
                data_in_zone = []
                d=data[0]
                while d.id == zone and data:
                    #As long as there's data left and the zone is current
                    #   data gets popped off the top of data and put in
                    #   data_in_zone
                    data_in_zone.append(data.pop(0))
                    if data:
                        d=data[0]

                if len(data_in_zone) < 5:
                    #If data is too short
                    continue
                elif not elided_zone_path or zone != elided_zone_path[-1]:
                        #If either the first zone or not the same as the previous zone
                        elided_zone_path.append(zone)
                elided_data.extend(data_in_zone)



            cut_pts = []
            for zone in elided_zone_path:
                dists_in_zone = []
                time_in_zone = []

                #For each all the points in each zone,
                d=elided_data[0]
                while d.id == zone:
                    dists_in_zone.append(d.s)
                    time_in_zone.append(d.t)
                    del elided_data[0]
                    if elided_data:
                        d=elided_data[0]
                    else:
                        break
                min_data_idx = dists_in_zone.index(min(dists_in_zone))
                if min(dists_in_zone) < 20:
                    cut_pts.append([zone, time_in_zone[min_data_idx]])

            # tqdm.write(str(cut_pts))
            for i in range(len(cut_pts)):
                if i != 0:
                    if cut_pts[i-1][0] < 0 or cut_pts[i][0] < 0:
                        tqdm.write("Outside of bounds, skipping path")
                        continue
                    if cut_pts[i-1][1] < 0 or cut_pts[i][1] < 0:
                        tqdm.write("Negative time in file: " +str(file))
                        continue
                    time_between = cut_pts[i][1] - cut_pts[i-1][1]
                    data_mtx[cut_pts[i-1][0]][cut_pts[i][0]].append(time_between/num_pts)


    np.save('time_data', data_mtx)
