import osmnx as ox
import networkx as nx
from typing import OrderedDict
from networkx import MultiDiGraph
import requests
import srtm
from termcolor import colored
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
            'lon', 'lat', 'length', 'grade', 'cycleway', 'footway'
        ]

        return ox.utils_graph.get_route_edge_attributes(graph, path)
    

    def get_surface_diffs(self, graph, paths: list, path_lengths: list, min_length_diff_routes_indeces, percentage_hard_input) -> dict:
        """
        Calculate the absolute difference between the surface distribution of each path and the inputted percentage of hard surfaces.
        
        Args
        ----------
        - self: Instance of the class.
        - graph: Graph containing nodes and edges.
        - paths: List of routes represented as nodes or edges.
        - path_lengths: List of corresponding lengths for each route.
        - min_length_diff_routes_indeces: List of indices of the routes that have minimal length difference.
        - percentage_hard_input: Inputted percentage of hard surfaces.

        Returns
        -------
        - dict: Dictionary where the keys are the indices of the paths and the values are the absolute differences between the surface distribution of the corresponding path and the inputted percentage of hard surfaces.
        """

        #most used tags according to https://taginfo.openstreetmap.org/keys/surface#values
        # hardened surfaces
        hardened_surfaces = [
            "asphalt", "paved", "concrete", "paving_stones", "sett",
            "concrete:plates", "cobblestone", "concrete:lanes", "metal",
            "grass_paver", "artificial_turf", "tartan", "unhewn_cobblestone",
            "concrete:flattened", "brick", "bricks", "acrylic", "chipseal",
            "metal_grid", "cement", "rubber", "hard"
        ]

        # unhardened surfaces
        unhardened_surfaces = [
            "unpaved", "ground", "gravel", "dirt", "grass", "compacted", "sand",
            "fine_gravel", "wood", "earth", "pebblestone", "mud", "rock", "stone",
            "woodchips", "dirt/sand", "soil", "trail", "plastic"
        ]
        
        surfaces_hard_percentage = {}
        #unhardenend is 100% - hardened%, obviously
        for path_index in min_length_diff_routes_indeces:
            analyzed_route = self.get_path_attributes(graph, paths[path_index])
            surfaces = self.get_path_surface_distribution(analyzed_route)

            for surface in hardened_surfaces:
                if surface in surfaces:
                    if path_index not in surfaces_hard_percentage:
                        #convert to meters and to percentage of full path
                        surfaces_hard_percentage[path_index] = surfaces[surface]*1000/path_lengths[path_index]
                    else:
                        surfaces_hard_percentage[path_index] += surfaces[surface]*1000/path_lengths[path_index]

        #update the dictionary so it contains the difference between the inputted percentage and the percentage of hard surfaces
        for key, value in surfaces_hard_percentage.items():
            #print("index: ", key, "hardened percentage: ", value)
            surfaces_hard_percentage[key] = abs(percentage_hard_input - value)
            
  
        return surfaces_hard_percentage

    def calculate_percentage_hardened_surfaces(self, graph, path: list, path_length: list) -> float: 
        """
        Calculate the percentage of hard surfaces in a path.

        Args
        ----------
        - self: Instance of the class.
        - graph: Graph containing nodes and edges.
        - path: Path within the graph for percentage calculation.

        Returns
        -------
        - float: Percentage of hard surfaces along the specified path.
        """
        # hardened surfaces
        hardened_surfaces = [
            'asphalt',
            'concrete',
            'paved',
            'sett',
            'tartan',
            'metal',
            'wood',
            'compacted',
            'bricks',
            'salt',
            'compacted',
            'unhewn_cobblestone',
            'paving_stones'
        ]

        # unhardened surfaces
        unhardened_surfaces = [
            'unpaved',
            'gravel',
            'dirt',
            'grass',
            'sand',
            'ground',
            'clay',
            'earth',
            'fine_gravel',
            'mud',
            'pebblestone',
            'unknown'
        ]          
        percentage_hardened: float = 0
        analyzed_route = self.get_path_attributes(graph, path)
        surfaces = self.get_path_surface_distribution(analyzed_route)

        for surface in hardened_surfaces:
            if surface in surfaces:     
                percentage_hardened += surfaces[surface]*1000/path_length
        return percentage_hardened

        
              
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


        # Get an amount of paths closest to the inputted leangth of the route
        min_length_diff_routes_indices = []
        sorted_indices = sorted(path_length_diff, key=path_length_diff.get)[:round(leafs/2)]  #increase te number to decrease the variation in the route length difference and increase the amount of evluated routes
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

            # Get the sum of all upwards elevation changes in the all paths
            elevation_diff = self.calculate_elevation_diff(graph, temp_path)
            #print("elevation difference: ", elevation_diff)

            # enter the difference between the elevation difference of the path and the inputted elevation difference into a dict with the index 
            # of the path in the paths list as key, this does not take into account the start node twice(this is added later on)
            height_diffs[path_index] = (abs(elevation_diff_input - elevation_diff))/elevation_diff_input
        return height_diffs
    

    def get_paths_and_path_lengths(self, graph, leaf_paths: list, start_node) -> list:
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
        paths = []
        path_lengths = []
        for temp_path in leaf_paths:
            path = []
            temp_path_lengths = []
            # Loop through all shortest paths between the point and add them to 1 path
            for i in range(0, len(temp_path) - 1):
                j = i + 1
                if j >= len(temp_path):
                    j = 0
                try:
                    temp_path_lengths.append(self.shortest_path_length(graph, temp_path[i], temp_path[j]))
                    for node in self.planner.shortest_path(graph, temp_path[i], temp_path[j]):
                        path.append(node)
                    # remove last node to prevent doubles ( start of next path is end of previous path)

                    path.pop(-1)
                    
                except nx.exception.NetworkXNoPath:
                    # No path, error
                    print(f"No path from {temp_path[i]} to {temp_path[j]}")
                    continue

            if path != []:
                #TODO: take out duplicate nodes between duplicate nodes maybe???

                #add the start node to the end to make a full circle
                path.append(start_node)

                paths.append(path)
                path_lengths.append(sum(temp_path_lengths) * 1000) 
        return paths, path_lengths
    
    def get_score_only_elevation(self, graph, paths, path_lengths, min_length_diff_routes_indeces, elevation_diff_input, max_length):
        """
        Args
        ----------
        - self: Instance of the class.
        - graph: Graph containing nodes and edges.
        - paths: List of routes.
        - path_lengths: List of corresponding lengths for each route.
        - min_length_diff_routes_indeces: List of indices of the routes that have minimal length difference to the input.
        - elevation_diff_input: Inputted elevation difference.
        - max_length: Inputted length of the route.


        Returns
        -------
        - dict: Dictionary where the keys are the indices of the paths in the "paths" list and the values are the scores of the corresponding paths. 
        """

        # remove "path_lengths[path_index]/max_length" from the score to leave out the length
        
        height_diffs = self.get_height_diffs(graph, paths, path_lengths, min_length_diff_routes_indeces, elevation_diff_input) #calcualte difference betwen input and outcome of height values
        paths_with_scores = {} #fill the dictionary with paths and scores, the lower the score the better the score indicates the difference between input and output
        for path_index in min_length_diff_routes_indeces:
            #the lower the score the better, (least difference with input)

            paths_with_scores[path_index] = height_diffs[path_index] + path_lengths[path_index]/max_length #add the scores together

            print(colored("path index (both): ", 'red'), path_index, colored(" score: ", 'red'), colored(paths_with_scores[path_index], "green"))
            print("______________________________________________________")
        return paths_with_scores

    def get_score_only_surface(self, graph, paths, path_lengths, min_length_diff_routes_indeces, percentage_hard_input, max_length):
        """
        Args
        ----------
        - self: Instance of the class.
        - graph: Graph containing nodes and edges.
        - paths: List of routes.
        - path_lengths: List of corresponding lengths for each route.
        - min_length_diff_routes_indeces: List of indices of the routes that have minimal length difference to the input.
        - percentage_hard_input: Inputted percentage of hard surfaces.
        - max_length: Inputted length of the route.

        Returns
        -------
        - dict: Dictionary where the keys are the indices of the paths in the "paths" list and the values are the scores of the corresponding paths.
        """

        # remove "path_lengths[path_index]/max_length" from the score to leave out the length

        percentage_hard_input /= 100 #make it a percentage
        surface_diffs = self.get_surface_diffs(graph, paths, path_lengths, min_length_diff_routes_indeces, percentage_hard_input) #calcualte difference betwen input and outcome of surface values
        paths_with_scores = {} #fill the dictionary with paths and scores, the lower the score the better the score indicates the difference between input and output
        for path_index in min_length_diff_routes_indeces:
            #the lower the score the better, (least difference with input)

            paths_with_scores[path_index] = surface_diffs[path_index] + path_lengths[path_index]/max_length #add the scores together

            print(colored("path index (both): ", 'red'), path_index, colored(" score: ", 'red'), colored(paths_with_scores[path_index], "green"))
            print("______________________________________________________")
    
        return paths_with_scores
    

    def get_score_elevation_and_surface(self, graph, paths, path_lengths, min_length_diff_routes_indeces, percentage_hard_input, elevation_diff_input, max_length):
        """
        Args
        ----------
        - self: Instance of the class.
        - graph: Graph containing nodes and edges.
        - paths: List of routes.
        - path_lengths: List of corresponding lengths for each route.
        - min_length_diff_routes_indeces: List of indices of the routes that have minimal length difference to the input.
        - percentage_hard_input: Inputted percentage of hard surfaces.
        - elevation_diff_input: Inputted elevation difference.
        - max_length: Inputted length of the route.

        Returns
        -------
        - dict: Dictionary where the keys are the indices of the paths in the "paths" list and the values are the scores of the corresponding paths.
        """

        # remove "path_lengths[path_index]/max_length" from the score to leave out the length
        
        paths_with_scores = {} #fill the dictionary with paths and scores, the lower the score the better the score indicates the difference between input and output
                
        height_diffs = self.get_height_diffs(graph, paths, path_lengths, min_length_diff_routes_indeces, elevation_diff_input) #calcualte difference betwen input and outcome of height values
        
        percentage_hard_input /= 100 #make it a percentage
        surface_diffs = self.get_surface_diffs(graph, paths, path_lengths, min_length_diff_routes_indeces, percentage_hard_input) #calcualte difference betwen input and outcome of surface values
        #TODO: should i really score like this??????
        for path_index in min_length_diff_routes_indeces:
            #the lower the score the better, (least difference with input)
            print("path index (both): ", path_index, " height diff between in/out put: ", height_diffs[path_index], " surface diff between in/out put: ", surface_diffs[path_index], " path length ", path_lengths[path_index])
            
            paths_with_scores[path_index] = height_diffs[path_index] + surface_diffs[path_index] + path_lengths[path_index]/max_length #add the scores together
            
            print(colored("path index (both): ", 'red'), path_index, colored(" score: ", 'red'), colored(paths_with_scores[path_index], "green"))
            print("______________________________________________________")

        return paths_with_scores


    