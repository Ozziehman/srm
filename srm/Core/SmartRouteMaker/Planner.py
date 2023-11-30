import osmnx as ox
from typing import Tuple, List
from networkx import MultiDiGraph
import math

class Planner:

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
    
    def calculate_start_point_index(self, flower_angle, points_per_leaf):
        # Calculate the index of the start point on the circle, based on the direction of the circle
        start_point_index = ((flower_angle * (180 / math.pi)) / 360) * points_per_leaf + (points_per_leaf / 2)

        if start_point_index >= points_per_leaf:
            start_point_index = start_point_index - points_per_leaf

        return start_point_index
    