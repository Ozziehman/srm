import osmnx as ox
from typing import Tuple, List
from networkx import MultiDiGraph
import math
import numpy as np

import srm.Core.SmartRouteMaker.Graph as Graph

class Planner:

    def __init__(self) -> None:
        self.graph = Graph.Graph()
        

    def shortest_path(self, graph: MultiDiGraph, start_node: int, end_node: int) -> List:
        """Get the shortest path between two nodes in a graph.

        Args:
            graph (MultiDiGraph): Instance of an osmnx graph.
            start_node (int): Unique ID of the start node within the graph.
            end_node (int): Unique ID of the end node within the graph.

        Returns:
            List: [xxx, yyy, zzz] A sequence of nodes that form the shortest path.
        """        

        return ox.shortest_path(graph, start_node, end_node)
    
    def calculate_start_point_index(self, flower_angle: float, points_per_leaf: int) -> float:
        """
        Calculates the index of the start point on a circular structure based on the specified flower angle and points per leaf.

        Args
        ----------
        - self: Instance of the class.
        - flower_angle: Angle (in radians) representing the desired direction of the circular structure.
        - points_per_leaf: Number of points or nodes in each leaf of the circular structure.

        Returns
        -------
        - float: Index of the start point on the circular structure.

        This function calculates the index of the start point on a circular structure based on the given flower angle
        and the number of points in each leaf. The angle is converted to degrees, and the index is determined by the
        proportion of the flower angle relative to the total circle. If the calculated index exceeds the total number of
        points per leaf, it wraps around to ensure a valid index is returned.

        Example
        -------
        start_index = calculate_start_point_index(my_flower_angle, 10)
        """
        # Calculate the index of the start point on the circle, based on the direction of the circle
        start_point_index = ((flower_angle * (180 / math.pi)) / 360) * points_per_leaf + (points_per_leaf / 2)

        if start_point_index >= points_per_leaf:
            start_point_index = start_point_index - points_per_leaf

        return start_point_index
    
    def calculate_leaf_nodes(self, flower_angle: float, start_node: int, radius: float, variance: float, points_per_leaf: int, graph: MultiDiGraph) -> list:
        """
        This method generates the nodes for each leaf in a flower-like pattern. Each iteration of this function rerurns 1 "incomplete" route.
        In the main function of the SmartRouteMaker, this function is called multiple times to generate multiple routes.

        Parameters
        ----------
        flower_angle (float): The angle of the flower pattern in radians.
        points_per_leaf (int): The number of points (nodes) to generate for each leaf.
        radius (float): The radius of each leaf in the flower pattern.
        variance (float): The variance in the radius of each leaf.
        start_node (int): The node ID of the start node.
        graph (networkx.Graph): The graph representing the area.

        Returns
        -------
        list: A list of node IDs representing the nodes for each leaf in the flower pattern.

        The method first calculates the center of each leaf based on the flower_angle, radius, and variance.
        It then generates a number of points (nodes) evenly spaced around the circumference of each leaf.
        The nodes are ordered in the list such that the start node is first (this happens in methods used within this method). 
        """
        #calculate where to put the start point in the circle
        start_point_index = self.calculate_start_point_index(flower_angle, points_per_leaf)

        flower_direction = flower_angle

        # Calculate the center of each leaf, based on the direction and the radius. Needs to be converted back to lon and lat, 111000 is the amount of meters in 1 degree of longitude/latitude
        difference_lon = math.cos(flower_direction) * radius * variance / 111000
        difference_lat = math.sin(flower_direction) * radius * variance / 111000

        leaf_center_lon = float(graph.nodes[start_node]["x"]) + float(difference_lon)
        leaf_center_lat = float(graph.nodes[start_node]["y"]) + float(difference_lat)

        # Get the node closest to the center of the leaf
        leaf_center_node = self.graph.closest_node(graph, (leaf_center_lat, leaf_center_lon)) # lat = y, lon = x

        # generate leaf angles depending on the number of leafs to be generated
        leaf_angles = np.linspace(0, 2 * np.pi, points_per_leaf)
        #create leaf nodes list for each leaf
        leaf_nodes = []
        # Create a circle around the current leaf_center_node an dcreate points on this leaf to make a route
        for leaf_angle in leaf_angles:

            leaf_direction = leaf_angle
            # Calculate the center of each leaf, based on the direction and the radius. Needs to be converted back to lon and lat, 111000 is the amount of meters in 1 degree of longitude/latitude
            difference_lon = math.cos(leaf_direction) * radius * variance / 111000
            difference_lat = math.sin(leaf_direction) * radius * variance / 111000

            leaf_node_lon = float(graph.nodes[leaf_center_node]["x"]) + float(difference_lon)
            leaf_node_lat = float(graph.nodes[leaf_center_node]["y"]) + float(difference_lat)

            leaf_node = self.graph.closest_node(graph, (leaf_node_lat, leaf_node_lon))

            leaf_nodes.append(leaf_node)

        # Get the list in the correct order with the start node included
        leaf_nodes = self.graph.insert_start_node_and_rearrange(leaf_nodes, start_node, start_point_index)
        #leaf paths only consist of the calculated nodes, these are later then converted to actual paths with all nodes
        return leaf_nodes
