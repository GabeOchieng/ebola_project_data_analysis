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

def distance(pt, node):
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

def find_first_change(node_id, prev_changes):
    # print(node_id)
    # print(prev_changes)
    for i, line in enumerate(prev_changes):
        # print(i, line)
        if line[1]== node_id and line[0] != 0:
            return prev_changes[i][0]

def show_path(pts, lastnode, node, mask, node_pts):
    fig = plt.figure()
    plt.ylim(2300, 1790)
    plt.xlim(1620, 2300)
    implot = plt.imshow(mask, cmap=plt.cm.nipy_spectral, Animated=True)

    for pt in pts:
        plt.scatter(pt[0], pt[1], c='b', marker='.')
        plt.draw()

    plt.scatter(node_pts[node][1],node_pts[node][0], c='g')
    plt.draw()
    plt.scatter(node_pts[lastnode][1],node_pts[lastnode][0], c='g')
    plt.draw()

    plt.show()

if __name__ == "__main__":
    path = os.getcwd() + '/'
    data_path = path + 'etu_1_condensed/courtyard_0_bed_20.p'
    # data_path = path + 'etu_1_condensed/test/'

    step = 1
    num_pts = 10

    node_pts = np.load(path + 'node_data.npy')[:,0].tolist()
    voronoi_mask = np.load(path + 'voronoi_expansion_mask.npy')

    poses = yaml.load(open(path + 'amcl_poses.yaml', 'rb'))
    map_params = yaml.load(open(path + 'map.yaml', 'rb'))
    origin = map_params['origin']
    res = map_params['resolution'] #meters per pixel
    I = Image.open(path + 'map.pgm')
    imarray = np.asarray(I).astype('int')
    w, h = I.size
    im_w = int(w/step)
    im_h = int(h/step)

    poses_dict = dict()
    for p in poses:
        poses_dict[p['name']] = p

    files = glob.glob(data_path)# + '*.p')

    #generate matrix for data
    data_mtx = [[[] for k in range(len(node_pts))] for i in range(len(node_pts))]

    tqdm.write("Getting path data")
    for file in tqdm(files, position = 0):
        dataset = pickle.load(open(file, 'rb'))

        if dataset == []:
            continue

        for trial in dataset:
            if trial[1] > 1000 or trial[0] == 4:
                # tqdm.write("bad trial " + str(file))
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

            fig = plt.figure()
            plt.ylim(2300, 1790)
            plt.xlim(1620, 2300)
            implot = plt.imshow(voronoi_mask, cmap=plt.cm.nipy_spectral, Animated=True)

            time = 0
            node_passed = False
            last_dist = []
            last_dist_change = False
            prev_changes = []
            prev_node_reg = -1
            zone_path = []
            started_in_zone = False

            pt_list = []

            for point in interpolated_data:
                #unpack points
                x_coord = point[0]
                y_coord = point[1]

                node_id = voronoi_mask[y_coord][x_coord]
                dist = distance((x_coord, y_coord), (node_pts[node_id][1],node_pts[node_id][0]))
                if node_id not in zone_path:
                    zone_path.append(node_id)

                tqdm.write(str((x_coord, y_coord)) + ' ' + str(dist))
                time +=1

                pt_list.append((x_coord, y_coord))
                plt.scatter([x_coord], [y_coord], c='b', marker='.')
                plt.scatter(node_pts[node_id][1],node_pts[node_id][0], c='g')
                plt.pause(.001)
                plt.draw()

                if node_id < 0:
                    #Outside of marked area
                    tqdm.write("outside of marked area")
                    continue

                if type(last_dist) is list:
                    #On first run, just set last_dist and last_node_id
                    #   the type is used because we care about when last_dist = 0
                    tqdm.write("First run in zone")
                    last_dist = dist
                    last_node_id = node_id

                    if dist < 20:
                        started_in_zone = True
                        time_before_zone = time
                        tqdm.write("starting in range " +str(started_in_zone) + ' ' + str(time_before_zone))
                    continue

                if node_id != last_node_id:
                    #If we've moved to a new zone, we need to reset our distances
                    tqdm.write("new zone")
                    last_dist = []
                    last_dist_change = False
                    last_node_id = node_id
                    prev_changes = []
                    continue

                #as long as we have valid distances to work with, we can set
                #   the distance change
                dist_change = dist-last_dist
                if dist_change == 0:
                    continue
                else:
                    # We only need to keep non-zero changes
                    prev_changes.append(dist_change)

                tqdm.write(str(node_id) + ' ' +str(dist_change))

                if last_dist_change == False:
                    #if last_dist_change hasn't been set, then it should
                    # tqdm.write("last_dist_change is 0")
                    #   be initialized
                    last_dist = dist
                    last_dist_change = dist_change
                    last_node_id = node_id
                    continue

                if len(prev_changes) < 2:
                    #Not enough data for a valid window, so we don't want to do
                    #   any checks for nodes
                    tqdm.write("not enough data to make determination")
                    continue

                tqdm.write(str(prev_changes))

                if (started_in_zone and prev_changes[-2] >= 0 and prev_changes[-1] >= 0):
                    if prev_node_reg != -1:
                        #This means our closest approach was when we entered the
                        #   zone
                        tqdm.write("Found node at beginning of zone")
                        tqdm.write(str(prev_node_reg) + ' ' + str(node_id) + ' ' + str((time_before_zone)/num_pts))

                        data_mtx[prev_node_reg][node_id].append((time_before_zone)/num_pts)
                        time -= time_before_zone
                        prev_node_reg = node_id
                        started_in_zone = False
                        plt.waitforbuttonpress()
                    else:
                        #This means we started near a node
                        tqdm.write("Found first node")
                        plt.waitforbuttonpress()
                        prev_node_reg = node_id
                        started_in_zone = False

                if dist < 20:
                    #Only check for node if you're within 20 px

                    if prev_changes[-2] <= 0 and prev_changes[-1] >= 0:
                        if prev_node_reg == -1:
                            #This is the first inflection point, so we can just start
                            #   timing
                            tqdm.write("Found first node")
                            plt.waitforbuttonpress()
                            time = 0
                            prev_node_reg = node_id
                            started_in_zone = False

                            # last_dist = dist
                            # last_dist_change = dist_change
                            # last_node_id = node_id
                            # continue
                        elif node_id != prev_node_reg:
                            tqdm.write("Found inflection")
                            tqdm.write(str(prev_changes[-2]) + ' ' + str(prev_changes[-1]))
                            tqdm.write(str(prev_node_reg) + ' ' + str(node_id) + ' ' + str(time/num_pts))
                            plt.waitforbuttonpress()
                            if prev_node_reg == 11 and node_id == 12:
                                tqdm.write(file)
                                show_path(pt_list, prev_node_reg, node_id, voronoi_mask, node_pts)
                            data_mtx[prev_node_reg][node_id].append(time/num_pts)
                            time = 0
                            prev_node_reg = node_id
                            started_in_zone = False

                last_dist = dist
                last_dist_change = dist_change
                last_node_id = node_id

    np.save('time_data', data_mtx)
