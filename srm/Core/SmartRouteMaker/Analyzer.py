import osmnx as ox
import networkx as nx
from typing import OrderedDict
from networkx import MultiDiGraph
import requests
import srtm

class Analyzer:

    def shortest_path_length(self, graph: MultiDiGraph, start_node: int, end_node: int) -> float:
        """Calculate the distance in meters of the shortest path.

        Args:
            graph (MultiDiGraph): Instance of an osmnx graph.
            start_node (int): Unique ID of the start node within the graph.
            end_node (int): Unique ID of the end node within the graph.

        Returns:
            float: Distance in kilometers of the shortest path.
        """        

        return round((nx.shortest_path_length(graph, start_node, end_node, weight="length") / 1000), 2)
    
    def get_path_surface_distribution(self, analyzedRoute: OrderedDict) -> dict:
        """Get the distribution of surface types within a route.

        Args:
            analyzedRoute (OrderedDict): Analysis of the route.

        Returns:
            dict: {'surface_name': 83.220, ...}
        """        

        surfaces = {}

        for edge in analyzedRoute:
            if "surface" in edge:
                if type(edge['surface']) == list:
                    edge['surface'] = edge['surface'][0]

                if edge['surface'] not in surfaces:
                    surfaces[edge['surface']] = edge['length'] 
                else:
                    surfaces[edge['surface']] = surfaces[edge['surface']]+ edge['length']
            else:
                if "unknown" not in surfaces:
                    surfaces['unknown'] = edge['length']
                else:
                    surfaces['unknown'] = surfaces['unknown'] + edge['length']

        for surface in surfaces:
            surfaces[surface] = round((surfaces[surface] / 1000), 2)

        return surfaces

    
    def get_path_attributes(self, graph: MultiDiGraph, path: list) -> OrderedDict:
        """Gets the attributes of a route.

        Args:
            graph (MultiDiGraph): Instance of an osmnx graph.
            path (list): Sequence of node ID's that form a route.

        Returns:
            OrderedDict: Attributes per edge of the route.
        """        

        ox.settings.useful_tags_way = [
            'bridge', 'tunnel', 'oneway', 'lanes', 'ref', 'name',
            'highway', 'maxspeed', 'service', 'access', 'area',
            'landuse', 'width', 'est_width', 'surface', 'junction',
            'lon', 'lat'
        ]

        return ox.utils_graph.get_route_edge_attributes(graph, path)
    
    def calculate_elevation_diff(self, graph, path) -> float:
        # get elevation DATA
        elevation_data = srtm.get_data()
        elevation_nodes = []

        # get elevation for each node from api
        for graphNode in path:
            node = graph.nodes[graphNode]
            nodeLat = node['y']
            nodeLon = node['x']

            try:
                elevation = elevation_data.get_elevation(nodeLat, nodeLon)
                elevation_nodes.append(elevation)
            except Exception as e:
                # Handle the case where getting elevation fails
                print(f"Error getting elevation for node {graphNode}: {e}")
                # You might want to log the error or take appropriate action.

        # calculate the elevation difference
        elevation_diff = 0
        for i in range(1, len(elevation_nodes)):
            try:
                diff = elevation_nodes[i] - elevation_nodes[i - 1]
                if diff > 0:
                    elevation_diff += diff
            except TypeError as e:
                # Handle the case where the subtraction resulted in a TypeError
                print(f"Error in elevation difference calculation: {e}")
                # You might want to log the error or take appropriate action.

        return elevation_diff

    
    def min_length_routes_indeces(self, paths, path_lengths, max_length, leafs) -> list:
        path_length_diff = {}
        # Find the path closest to the input of the user
        for i in range(len(paths)):
            path_length_diff[i] = abs(path_lengths[i] - max_length)

        print(path_length_diff)
        print("__________________________________________________________")

        # Get the 10 paths closest to the input length and save their indices
        min_length_diff_routes_indices = []
        sorted_indices = sorted(path_length_diff, key=path_length_diff.get)[:round(leafs/5)]  # Minimum 10
        min_length_diff_routes_indices.extend(sorted_indices)

        print(min_length_diff_routes_indices)
        print("__________________________________________________________")

        return min_length_diff_routes_indices
    

    