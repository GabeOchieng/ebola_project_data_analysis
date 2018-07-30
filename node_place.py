#!/usr/bin/env python3

#General Packages
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

#Packages to make life easier
from tqdm import tqdm, trange
import os
from PIL import Image

if __name__ == "__main__":
    path = os.getcwd() + '/'

    step=1
    I = Image.open(path + 'map.pgm')
    w, h = I.size
    im_w = int(w/step)
    im_h = int(h/step)

    skeleton = np.load(path + 'mask_data.npy')
    node_map = np.zeros((im_w, im_h), dtype=int)

    # plt.imshow(skeleton, cmap=cm.gray, interpolation='nearest')
    # plt.show()
    skel_pts = []
    tqdm.write("Finding nodes")
    for i in tqdm(range(im_h), position = 0):
        if i==0 or i==im_h-1:
            continue
        else:
            for j in range(im_w):
                if j == 0 or j==im_w-1:
                    continue
                else:
                    if skeleton[i][j] == 0:
                        continue
                    else:
                        skel_pts.append((i, j))
                        if skeleton[i-1][j-1] == 1:
                            node_map[i][j]+=1
                        if skeleton[i-1][j] == 1:
                            node_map[i][j]+=1
                        if skeleton[i-1][j+1] == 1:
                            node_map[i][j]+=1
                        if skeleton[i][j-1] == 1:
                            node_map[i][j]+=1
                        if skeleton[i][j+1] == 1:
                            node_map[i][j]+=1
                        if skeleton[i+1][j-1] == 1:
                            node_map[i][j]+=1
                        if skeleton[i+1][j] == 1:
                            node_map[i][j]+=1
                        if skeleton[i+1][j+1] == 1:
                            node_map[i][j]+=1

    node_pts = [[],[]]
    for i in trange(im_h, position = 0):
        for j in range(im_w):
            if node_map[i][j] == 0:
                continue
            if node_map[i][j] == 2:
                node_map[i][j] = 0
            if node_map[i][j] == 1 or node_map[i][j] > 2:
                node_pts[0].append((i, j))
                node_pts[1].append(node_map[i][j])

    np.save('node_pts', node_pts)
    np.save('skel_pts', skel_pts)
    # print(node_pts)
    # plt.imshow(skeleton, cmap=cm.gray, interpolation='nearest')
    # plt.imshow(node_map, cmap=cm.binary, interpolation='nearest')
    plt.scatter(*zip(*skel_pts), marker='.')
    plt.scatter(*zip(*node_pts[0]), s=45, marker='x', c='red')
    for i in range(len(node_pts[0])):
        plt.annotate(str(i), node_pts[0][i])
    # plt.show()
    plt.savefig('nodes.png', dpi=150)
