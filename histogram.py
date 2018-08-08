#!/usr/bin/env python3

#General Packages
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

data_mtx = np.load('time_data.npy')
node_cons = np.load('node_data.npy')
open('logs/bad_path_log.txt', 'w')
logfile = open('logs/bad_path_log.txt', 'a')
print(node_cons)
legends = []
for i, row in enumerate(data_mtx):
    for j, data in enumerate(row):
        if j in node_cons[i][1]:
            plt.hist(data)
            plt.title("Path from " + str(i) + ' to ' + str(j))
            plt.xlabel("Seconds")
            plt.ylabel("Number of runs")
            # legends.append(str(i) + ' ' + str(j))
            # plt.legend(legends, loc=5)
            # plt.show()
        elif len(data):
            logfile.write("Invalid path from " + str(i) + ' to ' + str(j) + ', count: ' + str(len(data)) + '\n')
plt.show()
