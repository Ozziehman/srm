from ...SmartRouteMaker import Graph
import numpy as np
import math
from typing import Tuple
import math
import numpy as np

class test():
    def __init__(self) -> None:
        """Initialize the facade.
        """        
        self.graph = Graph.Graph()
        
        # Own algorithm here, flower idea
    def plan_circular_route_flower(self, start_coordinates, max_length: int, options: dict) -> dict:
        """Generates a flower like structure on a given graph with circles
        which centers are N NE NW S SE SW E W of the starting node. On each circle the algorithm
        places 4 (or more, depending on future ideas) point which are used for making a route."""

        leafs = 8
        points_per_leaf = 4
        # Load the graph
        graph = self.graph.full_geometry_point_graph(start_coordinates)

        # Determine the start node based on the start coordinates
        start_node = self.graph.closest_node(graph, start_coordinates)

        # Has impact on the size of the circles(leafs)
        variance = 1

        # Generate array of 360 equal sized angles, basically a circle, duhh
        angle = np.linspace(0, 2 * np.pi, 360)

        # directions: 0, 45, 90, 135, 180, 225, 270, 315 (E SE S SW W NW N NE) each direction generate a circle
        for i in range (0, leafs):
            direction = angle[i*(360/leafs)]
            
            # Calculate how far to go in a direction according to the given length of the route
            radius = (max_length) / (2 * math.pi)

            # Calculate the center of each leaf, based on the direction and the radius. Needs to be converted back to lon and lat
            difference_lat = math.sin(direction) * radius * variance / 111000
            difference_lon = math.cos(direction) * radius * variance / 111000
            
            leaf_center_lat = float(graph.nodes[start_node]["x"]) + float(difference_lon)
            leaf_center_lon = float(graph.nodes[start_node]["y"]) + float(difference_lat)
            

            leaf_nodes = []

            # Get the node closest to the center of the leaf and place irt as the first int he path
            leaf_center_node = self.graph.closest_node(graph, (leaf_center_lat, leaf_center_lon)) # lat = y, lon = x
            if leaf_center_node not in leaf_nodes:
                leaf_nodes.append(leaf_center_node)
            
            # Generate the desired number of points on the circle and calculate the corresponding node
            angle = np.linspace(0, 2 * np.pi, points_per_leaf)

            # Create a circle around the current leaf_center_node, and create points on this leaf to make a route
            for i in angle:
                degree = i
                # Calculate the node on the circle(leaf) with lat and lon
                difference_lon = math.cos(degree) * radius / 111000
                difference_lat = math.sin(degree) * radius / 111000
                leaf_node_lat = float(graph.nodes[ leaf_center_node]["y"]) + float(difference_lat)
                leaf_node_lon = float(graph.nodes[ leaf_center_node]["x"]) + float(difference_lon)
                leaf_node = self.graph.closest_node(graph, (leaf_node_lat, leaf_node_lon))
                if leaf_node not in leaf_nodes:
                    leaf_nodes.append(leaf_node)
                

            # create empty leaf path to fill
            leaf_path = []

            # Create a path between the nodes on the leaf
            for i in range(len(leaf_nodes)-1):
                leaf_path.append(self.planner.shortest_path(graph, leaf_nodes[i], leaf_nodes[i+1]))

            print(leaf_path)

    def normalize_coordinates(self, coordinates: str, delimiter: str = ",") -> Tuple:
        """Converts a front-end inputted coordinate string into a tuple of two floats.

        Args:
            coordinates (str): String of two delimited coordinates
            delimiter (str, optional): The delimiter. Defaults to ",".

        Returns:
            Tuple: (x.xx, y.yy) tuple of normalized coordinates.
        """

        return tuple([float(coordinate.strip()) for coordinate in coordinates.split(delimiter)])  

    plan_circular_route_flower(normalize_coordinates("50.966200, 5.829650"), 1000, {})



        