./cluster_and_skel2.py
eog cont_skel_2.png &
./node_place.py
./generate_graph.py
eog reduced_graph.png &
rm -r gif_imgs/*
./voronoi_expansion.py
./make_gif.py
./pathfinder8.py
./histogram.py

