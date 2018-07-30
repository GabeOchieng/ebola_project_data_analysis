#!/usr/bin/env python3

#General Packages
import numpy as np
from scipy import ndimage
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import matplotlib.cm as cm

#Data analysis modules
from skimage.morphology import medial_axis
from sklearn.cluster import KMeans

#Packages to make life easier
from tqdm import tqdm, trange
import os
from PIL import Image
import yaml, glob, pickle
import animation


def extract_data(im_w, im_h, origin, res, files):
    im = np.zeros((im_w,im_h), dtype=int)

    for file in tqdm(files, position = 0):
        dataset = pickle.load(open(file, 'rb'))
        for trial in dataset:
            if trial[1] > 1000:
                continue
            for point in trial[2]:
                x = point.position.x - origin[0]
                y = point.position.y - origin[1]
                x_coord = int(x/res)
                y_coord = im_h - int(y/res)

                im[y_coord,x_coord] = im[y_coord,x_coord] + 1

    return im

def make_bmap(im, im_w, im_h, thresh_chk):
    im_thresh = np.zeros((im_w, im_h), dtype=int)

    if thresh_chk == 0:
        thresh = 0
    else:
        ct_dist = []
        for i in np.ndarray.flatten(im):
            if i != 0:
                ct_dist.append(i)
        thresh = np.percentile(ct_dist, thresh_chk)

    # tqdm.write("Thresholding at", thresh)

    i = 0
    for row in im:
        im_thresh[i] = [0 if i <=thresh else 1 for i in row]
        i+=1

    return im_thresh

if __name__ == "__main__":


    cwd = os.getcwd()
    map_path = cwd + '/'
    # data_path = cwd + '/etu_1_condensed/test/'
    data_path = cwd + '/etu_1_condensed/'
    log = open('logs/log_file.txt', 'w')
    open('logs/extraction_log.txt', "w")
    open('logs/cluster_log.txt', "w")
    open('logs/generation_log.txt', "w")


    step = 1

    poses = yaml.load(open(map_path + 'amcl_poses.yaml', 'rb'))
    map_params = yaml.load(open(map_path + 'map.yaml', 'rb'))
    origin = map_params['origin']
    res = map_params['resolution'] #meters per pixel
    I = Image.open(map_path + 'map.pgm')
    w, h = I.size
    im_w = int(w/step)
    im_h = int(h/step)

    files = glob.glob(data_path + '*.p')

    tqdm.write("Extracting Data")
    im = extract_data(im_w, im_h, origin, res, files)


    wait = animation.Wait(text = 'Skeletonizing\n')
    wait.start()
    mask = make_bmap(im, im_w, im_h, 0)
    skel, distance = medial_axis(mask, return_distance=True)
    dist_on_skel = distance * skel
    wait.stop()

    dist_on_skel_filter = ndimage.filters.gaussian_filter(dist_on_skel, 6)
    # plt.imshow(dist_on_skel_filter, cmap=plt.cm.nipy_spectral, interpolation='nearest')
    # plt.show()

    wait = animation.Wait(text = 'Skeletonizing again\n')
    wait.start()
    mask2 = make_bmap(dist_on_skel_filter, im_w, im_h, 90)
    # plt.imshow(mask2, cmap=plt.cm.nipy_spectral, interpolation='nearest')
    # plt.show()

    skel2, dist2 = medial_axis(mask2, return_distance=True)
    dist_on_skel_2 = dist2 * skel2
    mask3 = make_bmap(dist_on_skel_2, im_w, im_h, 0)

    np.save('mask_data', mask3)
    wait.stop()

    # plt.contour(mask, [0.5], colors='w')
    # plt.imshow(dist_on_skel_2, cmap=plt.cm.nipy_spectral, interpolation='nearest')
    # plt.show()
    #
    plt.imsave('cont_skel_blur.png', dist_on_skel_filter, cmap=plt.cm.nipy_spectral)
    plt.imsave('cont_skel_2.png', dist_on_skel_2, cmap=plt.cm.nipy_spectral)


    ############STEPS##########
    #1. Get data (done)
    #2. Cluster data (done)
    #3. Find center velocities (done)
    #4. Order centers (done)
    #5. Interpolate path data (done)
    #6. Generate bitmap (done)
    #7. Skeletonize (done)
    #8. Place nodes (done)
    #9. Reduce nodes (done)
