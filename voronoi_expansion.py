#!/usr/bin/env python3

#General Packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from copy import deepcopy


#Packages to make life easier
import os, time
from tqdm import tqdm, trange
from PIL import Image

class Node:
    def __init__(self,point,id):
        self.pt = point
        # self.parent = parent
        self.id = id


def neighbors(pt, mask):
    neighbor_list = [(pt[0]-1, pt[1]), (pt[0]+1, pt[1]), (pt[0], pt[1]-1), (pt[0], pt[1]+1)]
    neighbor_list = [point for point in neighbor_list if mask[point[0]][point[1]] == -1]
    return neighbor_list

def method(node_pts, mask, openpts):
    openset = {}
    # closedset = set()
    # openset = []
    for pt in node_pts:
        # openset.append([(pt[0], pt[1]), node_pts.index(pt)])
        openset[(pt[0], pt[1])] = node_pts.index(pt)

    i = 0
    # plt.ion()
    # fig = plt.figure()
    # plt.ylim(2300, 1790)
    # plt.xlim(1620, 2300)
    # aoi = mask[np.ix_(np.arange(1790,2400,1), np.arange(1620,2300,1))]

    # plt.imshow(aoi, cmap=cm.nipy_spectral)

    # plt.show()
    # plt.pause(1)

    # plt.imsave('test.png', aoi, cmap=cm.nipy_spectral)
    tqdm.write("Building voronoi tesselation")
    pbar = tqdm(total = openpts)
    while openset:
        opencop = dict(openset)
        for pt in opencop:
            # pt = line[0]
            # id = line[1]
            id = opencop[pt]
            mask[pt[0]][pt[1]] = id
            for n in neighbors(pt, mask):
                # openset.append([n, id])
                openset[n] = id
            del openset[pt]
            # del openset[0]

            pbar.update(1)
        # tqdm.write(str(len(openset)))
        del opencop

        i+=1

        # plt.pause(.05)
        # plt.draw()
        # im.set_data(mask)
        # plt.savefig('gif_imgs/voronoi_expansion_anim_' + str(i) + '.png')
        aoi = mask[np.ix_(np.arange(1740,2450,1), np.arange(1600,2400,1))]
        plt.imsave('gif_imgs/voronoi_expansion_anim_' + str(i) + '.png', aoi, cmap=cm.nipy_spectral)
    return mask


if __name__ == "__main__":
    path = os.getcwd() + '/'
    # data_path = path + 'etu_1_data/etu_1_condensed/'
    data_path = path + 'etu_1_condensed/test/'

    node_data = np.load(path + 'node_data.npy')
    node_pts = node_data[:,0].tolist()

    I = Image.open(path+'map.pgm')
    w, h = I.size
    p = np.asarray(I).astype('int')
    mask = np.asarray([[-2]*len(p[0])]*len(p))

    openpts = 0
    tqdm.write('Generating mask')
    for i in trange(len(p), position=0):
        for j in range(len(p[i])):
            if p[i][j] == 254:
                #-1 is unassigned
                mask[i][j] = -1
                openpts += 1

    mask = method(node_pts, mask, openpts)

    plt.imsave('voronoi_expansion_mask.png', mask, cmap=cm.nipy_spectral)
    # plt.show()
    np.save('voronoi_expansion_mask', mask)
