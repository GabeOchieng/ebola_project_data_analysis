#!/usr/bin/env python3

#General Packages
import numpy as np
import matplotlib.pyplot as plt

#Packages to make life easier
import os
from tqdm import tqdm


def find_adjacent(pt, skeleton):
    pt_list = []

    if skeleton[pt[0]-1][pt[1]-1] == 1:
        pt_list.append((pt[0]-1,pt[1]-1))
    if skeleton[pt[0]-1][pt[1]] == 1:
        pt_list.append((pt[0]-1,pt[1]))
    if skeleton[pt[0]-1][pt[1]+1] == 1:
        pt_list.append((pt[0]-1, pt[1]+1))
    if skeleton[pt[0]][pt[1]-1] == 1:
        pt_list.append((pt[0], pt[1]-1))
    if skeleton[pt[0]][pt[1]+1] == 1:
        pt_list.append((pt[0], pt[1]+1))
    if skeleton[pt[0]+1][pt[1]-1] == 1:
        pt_list.append((pt[0]+1, pt[1]-1))
    if skeleton[pt[0]+1][pt[1]] == 1:
        pt_list.append((pt[0]+1, pt[1]))
    if skeleton[pt[0]+1][pt[1]+1] == 1:
        pt_list.append((pt[0]+1, pt[1]+1))

    return pt_list

def generate_node_connections(node_pts):
    node_num = len(node_pts[0])
    connection_mtx = np.zeros((node_num, node_num), dtype=int)

    #Generate matrix of connection lengths, 0 is no connection
    for i, pt in enumerate(node_pts[0]):
        path_list = find_adjacent(pt, skeleton)

        for p, path_start in enumerate(path_list):
            cur_p = path_start
            last_p = pt

            path_length = 1
            while cur_p not in node_pts[0]:
                paths = find_adjacent(cur_p, skeleton)
                if len(paths) > 2:
                    print("This point has too many adjacent points")
                    break
                paths.remove(last_p)
                last_p = cur_p
                cur_p = paths[0]
                path_length+=1

            node_idx = node_pts[0].index(cur_p)
            connection_mtx[i][node_idx] = path_length

    # print('\n'.join([''.join(['{:3}'.format(item) for item in row]) for row in connection_mtx]))

    #Convert from matrix to list of connections and lengths
    node_connection_list = [[],[],[],[]]
    for i, pt in enumerate(node_pts[0]):
        nz = np.nonzero(connection_mtx[i])[0]
        node_connection_list[0].append(nz)
        node_connection_list[1].append(connection_mtx[i][nz])
        node_connection_list[2].append(i)
        node_connection_list[3].append(node_pts[0][i])

    return np.transpose(node_connection_list).tolist()

def generate_node_idx_mapping(node_connection_list):
    #generate a list of where each node is
    node_idx_mapping = []
    j = 0
    for i in range(node_connection_list[-1][2]+1):
        if i == node_connection_list[j][2]:
            node_idx_mapping.append(j)
            j+=1
        else:
            node_idx_mapping.append(0)

    return node_idx_mapping


if __name__ == "__main__":
    path = os.getcwd() + '/'

    skeleton = np.load(path + 'mask_data.npy')
    node_pts = np.load(path + 'node_pts.npy').tolist()

    node_connection_list = generate_node_connections(node_pts)
    for i, row, in enumerate(node_connection_list):
        node_connection_list[i][0] = row[0].tolist()
        node_connection_list[i][1] = row[1].tolist()


    node_connection_copy = node_connection_list
    node_deletion_list = []


    #This loop looks at nodes with only one connection. If two nodes are solely
    #   connected, both can be deleted. If a node has a very short connection,
    #   then we can also delete that
    for i, row in enumerate(node_connection_list):
        #For these cases that need to be reduced, we will delete the current node
        if len(row[0]) == 1:
            #find nodes which are only connected to each other and delete
            if len(node_connection_list[row[0][0]][0]) == 1:
                node_deletion_list.append(i)

            #if we're already in a place where there's only one connection
            #   we can see if that connection is short, which means that this
            #   node is the end of a "spur" path
            elif row[1][0] <= 15:
                node_deletion_list.append(i)
                # if the other end of that connection has 2  remaining connections,
                #   then it is no longer a node, so we need to delete it and
                #   rewire the nodes on either side to connect to each other
                if len(node_connection_list[row[0][0]][0]) == 3:
                    del_node = row[0][0]
                    node_deletion_list.append(del_node)

                    del_info = node_connection_copy[del_node][0]
                    del_info.remove(i)

                    node_connection_copy[del_info[0]][0].append(del_info[1])
                    node_connection_copy[del_info[1]][0].append(del_info[0])
                    #append 0 to the length, just to keep the lengths the same
                    node_connection_copy[del_info[0]][1].append(0)
                    node_connection_copy[del_info[1]][1].append(0)

    #This loop removes clustered nodes (defined as being within 3
    #   pixels of each other, by a pretty much random choice) and then
    #   rewire the relevant connections. It shouldn't matter which of the nodes
    #   gets deleted, so we'll keep the current node and delete the others
    for i, row in enumerate(node_connection_list):
        if i not in node_deletion_list:
            close_node_idx = [j for j, dist in enumerate(row[1]) if dist < 4 and dist > 0]

            for j in range(len(close_node_idx)):
                #this is unnecessary, but makes it so much more straightforward
                del_node =  row[0][close_node_idx[j]]
                node_deletion_list.append(del_node)

                #For each node del_node is connected to, add i to their connections
                #   and add that node to i's connections
                for k in range(len(node_connection_list[del_node][0])):
                    if i != node_connection_list[del_node][0][k]:
                        new_con_node = node_connection_list[del_node][0][k]
                        node_connection_copy[i][0].append(new_con_node)
                        node_connection_copy[new_con_node][0].append(i)
                        #append 0 to the length, just to keep the lengths the same
                        node_connection_copy[i][1].append(0)
                        node_connection_copy[new_con_node][1].append(0)

    node_deletion_list = list(set(node_deletion_list))
    # print("nodes to be deleted", node_deletion_list)

    #delete extraneous nodes from the list of node points
    node_connection_list = [i for j, i in enumerate(node_connection_copy) if j not in node_deletion_list]

    for i in range(len(node_connection_list)):
        row_del_list = []
        for j in range(len(node_connection_list[i][0])):
            if node_connection_list[i][0][j] in node_deletion_list:
                row_del_list.append(j)
        node_connection_list[i][0] = [i for j, i in enumerate(node_connection_list[i][0]) if j not in row_del_list]
        node_connection_list[i][1] = [i for j, i in enumerate(node_connection_list[i][1]) if j not in row_del_list]

    #Check for self connections... I'm not entirely sure how this happens,
    #   but sometimes a node can get connected to itself, which then makes the
    #   final reduction in the next step not work
    for i, row in enumerate(node_connection_list):
        node_connection_list[i][0] = list(set(row[0]))



    #Final step to clean up connections for areas where there were stub
    #   paths connected to clusters. After this step, the path lengths no
    #   longer have correct array lengths
    last_node = node_connection_list[-1][2]
    node_idx_mapping = generate_node_idx_mapping(node_connection_list)
    i = 0
    row = node_connection_list[0]
    while row[2] != last_node:
        row = node_connection_list[i]
        if len(row[0]) == 2:
            node_1 = node_idx_mapping[row[0][0]]
            node_2 = node_idx_mapping[row[0][1]]

            node_connection_list[node_1][0].append(row[0][1])
            node_connection_list[node_2][0].append(row[0][0])

            node_connection_list[node_1][1].append(0)
            node_connection_list[node_2][1].append(0)

            node_connection_list[node_1][0].remove(row[2])
            node_connection_list[node_2][0].remove(row[2])

            del node_connection_list[node_idx_mapping[row[2]]]
            node_idx_mapping = generate_node_idx_mapping(node_connection_list)
            i+=-1
        i+=1

    #Redo node connections so that the indexes match the connections
    node_idx_mapping = generate_node_idx_mapping(node_connection_list)
    node_data = []
    for row in node_connection_list:
        node_data.append(np.array([row[3], row[0]], dtype=object))

    for i, row in enumerate(node_data):
        for j, val in enumerate(row[1]):
            node_data[i][1][j] = node_idx_mapping[val]

    np.save('node_data', node_data)
    for i, row in enumerate(node_data):
        print(i, row)
    node_pts_new = [row[3] for row in node_connection_list]
    np.save('node_pts_new', node_pts_new)
    skel_pts = np.load('skel_pts.npy')

    for row in tqdm(skel_pts):
        plt.scatter(row[1], row[0], marker='.', c='blue')
    for row in node_pts_new:
        plt.scatter(row[1], row[0], s=45, marker='x',c='red')
    plt.gca().invert_yaxis()
    for i in range(len(node_connection_list)):
        plt.annotate(str(i), (node_data[i][0][1],node_data[i][0][0]))
    plt.savefig("reduced_graph.png", dpi = 300)
