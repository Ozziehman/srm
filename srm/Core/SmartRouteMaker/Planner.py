import osmnx as ox
from typing import Tuple, List
from networkx import MultiDiGraph

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