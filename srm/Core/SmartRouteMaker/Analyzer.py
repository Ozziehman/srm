import osmnx as ox
import networkx as nx
from typing import OrderedDict
from networkx import MultiDiGraph
import requests
import srtm
from srm.Core.SmartRouteMaker import Planner

class Analyzer:
    #get the planner in here to use the shortest path function
    def __init__(self) -> None:
        self.planner = Planner.Planner()

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
        """
        Calculates the total positive elevation difference along a specified path within a graph.

        Args
        ----------
        - self: Instance of the class.
        - graph: Graph containing nodes and edges.
        - path: Path within the graph for elevation difference calculation.

        Returns
        -------
        - float: Total positive elevation difference along the specified path.

        This function utilizes elevation data, from the SRTM dataset to retrieve elevation
        values for nodes in the given path. It then calculates the positive elevation differences
        between adjacent nodes and returns the total sum. 

        Example
        -------
        elevation_difference = calculate_elevation_diff(my_graph_instance, my_path)
        """
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
                # Handle case where getting elevation gioes wrong
                print(f"Error getting elevation for node {graphNode}: {e}")

        # calculate the elevation difference
        elevation_diff = 0
        for i in range(1, len(elevation_nodes)):
            try:
                diff = elevation_nodes[i] - elevation_nodes[i - 1]
                if diff > 0:
                    elevation_diff += diff
            except TypeError as e:
                # Handle error 
                print(f"Error in elevation difference calculation: {e}")

        return elevation_diff

    
    def min_length_routes_indeces(self, paths, path_lengths, max_length, leafs) -> list:
        """
        Identifies and returns the indices of the routes with lengths closest to a specified maximum length.

        Args
        ----------
        - self: Instance of the class.
        - paths: List of routes represented as nodes or edges.
        - path_lengths: List of corresponding lengths for each route.
        - max_length: Inputted length of the route.
        - leafs: Number of total generated routes.

        Returns
        -------
        - list: Indices of the routes with lengths closest to the specified maximum length this is contextual to the paths list.

        This function returns the leafs/5 routes with lengths closest to the specified maximum length.

        Example
        -------
        route_indices = min_length_routes_indeces(my_paths, my_lengths, max_allowed_length, leafs = 15)
        """
        path_length_diff = {}
        # Find the path closest to the input of the user
        for i in range(len(paths)):
            path_length_diff[i] = abs(path_lengths[i] - max_length)


        # Get the 10 paths closest to the input length and save their indices
        min_length_diff_routes_indices = []
        sorted_indices = sorted(path_length_diff, key=path_length_diff.get)[:round(leafs/5)]  # Minimum 10
        min_length_diff_routes_indices.extend(sorted_indices)

        print("Routes closest in length: ", min_length_diff_routes_indices)
        print("__________________________________________________________")

        return min_length_diff_routes_indices
    
    def get_height_diffs(self, graph, paths, path_lengths, min_length_diff_routes_indeces, elevation_diff_input) -> dict:
        """
        Calculate the absolute difference between the elevation difference of each path and the inputted elevation difference.

        Parameters
        ----------
        graph (networkx.Graph): The graph representing the area.
        paths (list): A list of paths, where each path is a list of node IDs.
        path_lengths (list): A list of the lengths of each path.
        min_length_diff_routes_indeces (list): A list of indices of the paths that have minimal length difference.
        elevation_diff_input (float): The desired elevation difference.

        Returns
        -------
        dict: A dictionary where the keys are the indices of the paths and the values are the absolute differences between the elevation difference of the corresponding path and the inputted elevation difference.

        The method calculates the elevation difference for each path in min_length_diff_routes_indeces, and then calculates the absolute difference between this elevation difference and the inputted elevation difference. These differences are stored in a dictionary, which is then returned.
        """
        height_diffs = {}

        #calculate the elevation difference for each path and save it in a dict with the index of the path in the paths list as key
        #from now on look at only close mathces on length of the route to the user input
        for path_index in min_length_diff_routes_indeces:
            temp_path = paths[path_index]
            path_length = path_lengths[path_index]

            print("path length (closest to input) meter: ", path_length)

            # Get the sum of all upwards elevation changes in the all paths
            elevation_diff = self.calculate_elevation_diff(graph, temp_path)
            print("elevation difference: ", elevation_diff)

            # enter the difference between the elevation difference of the path and the inputted elevation difference into a dict with the index 
            # of the path in the paths list as key, this does not take into account the start node twice(this is added later on)
            height_diffs[path_index] = abs(elevation_diff_input - elevation_diff)
            print("__________________________________________________________")
        return height_diffs
    

    def get_paths_and_path_lengths(self, graph, leaf_paths: list) -> list:
        """Gets the paths and path lengths from a list of leaf paths

        Args
        ----
            graph (MultiDiGraph): Instance of an osmnx graph.
            leaf_paths (list): List of leaf paths.

        Returns
        -------
            paths (list): List of paths.
            path_lengths (list): List of path lengths.

        The indices of the two lists match woith eachother.

            """
        #TODO make this function multiprocessed
        paths = []
        path_lengths = []
        for temp_path in leaf_paths:
            path = []
            temp_path_lengths = []
            # Loop through all shortest paths between the point and add them to 1 path (cyclus)
            for i in range(0, len(temp_path) - 1):
                j = i + 1
                if j >= len(temp_path):
                    j = 0
                try:
                    temp_path_lengths.append(self.shortest_path_length(graph, temp_path[i], temp_path[j]))
                    for node in self.planner.shortest_path(graph, temp_path[i], temp_path[j]):
                        path.append(node)
                    # remove last node because the last in the final casce it adds the last and the last
                    path.pop(-1)
                    
                except nx.exception.NetworkXNoPath:
                    # No path, error
                    print(f"No path from {temp_path[i]} to {temp_path[j]}")
                    continue

            if path != []:
                #TODO: take out duplicate nodes between duplicate nodes maybe???
                paths.append(path)
                path_lengths.append(sum(temp_path_lengths) * 1000) 
        return paths, path_lengths

    