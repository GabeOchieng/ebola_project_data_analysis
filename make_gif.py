#!/usr/bin/env python3

#General Packages
import imageio
import os
import re
import glob
from tqdm import tqdm
import animation

path = os.getcwd() + '/gif_imgs/'

files = sorted(glob.glob( os.path.join(path, '*.png') ),key=lambda x:float(re.findall("([0-9]+?)\.png",x)[0]))

# files = sorted(glob.glob( path),key=lambda x:float(path.basename(x).split("_")[3]))

seq = []

tqdm.write("Generating frame sequence")
for file in tqdm(files):
    seq.append(imageio.imread(file))

wait = animation.Wait('spinner', text='Writing gif  ')
wait.start()
imageio.mimwrite('voronoi_expansion_anim.gif', seq, duration = .02)
wait.stop()
