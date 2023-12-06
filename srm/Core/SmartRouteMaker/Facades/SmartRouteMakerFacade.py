import time
from typing import Tuple
import math
import numpy as np
import multiprocessing as mp
from networkx import MultiDiGraph
from functools import partial


from ...SmartRouteMaker import Analyzer
from ...SmartRouteMaker import Visualizer
from ...SmartRouteMaker import Graph
from ...SmartRouteMaker import Planner

class SmartRouteMakerFacade():

    def __init__(self) -> None:
        """Initialize the facade.
        """        

        self.analyzer = Analyzer.Analyzer()
        self.visualizer = Visualizer.Visualizer()
        self.graph = Graph.Graph()
        self.planner = Planner.Planner()

    # Route
    def plan_route(self, start_coordinates: tuple, end_coordinates: tuple, options: dict) -> dict:
        """Plan a route between two coordinates.

        Args:
            start_coordinates (tuple): Tuple of two coordinates that represent the start point.
            end_coordinates (tuple): Tuple of two coordinates that represent the end point.
            options (dict): Analysis options, see the documentation.

        Returns:
            dict: Route and analysis data.
        """        

        graph = self.graph.full_geometry_point_graph(start_coordinates)

        # Get start/end nodes closest to the coordinates filled in the form
        start_node = self.graph.closest_node(graph, start_coordinates)
        end_node = self.graph.closest_node(graph, end_coordinates)

        # Get shortest path between start and end node
        path = self.planner.shortest_path(graph, start_node, end_node)
        

        elevation_nodes = self.analyzer.calculate_elevation_diff(graph, path)

        path_length = self.analyzer.shortest_path_length(graph, start_node, end_node)

        if "analyze" in options and options['analyze']:
            route_analysis = self.analyzer.get_path_attributes(graph, path)
        else:
            route_analysis = None
        
        if "surface_dist" in options and options['surface_dist']:
            surface_dist = self.analyzer.get_path_surface_distribution(route_analysis)
            surface_dist_visualisation = self.visualizer.build_surface_dist_visualisation(route_analysis, graph)

            surface_dist_legenda = {}

            for type in surface_dist:
                surface_dist_legenda[type] = (self.visualizer.get_surface_color(type))
        else:
            surface_dist = None
            surface_dist_visualisation = None
        
        simple_polylines = self.visualizer.extract_polylines_from_folium_map(graph, path, invert=False)
        output = {
            "start_node": start_node,
            "end_node": end_node,
            "path": path,
            "path_length": path_length,
            "route_analysis": route_analysis,
            "surface_dist": surface_dist,
            "surface_dist_visualisation": surface_dist_visualisation,
            "surface_dist_legenda": surface_dist_legenda,
            "simple_polylines": simple_polylines,
            "elevation_nodes": elevation_nodes
        }

        return output

    def calculate_leaf_path(self, flower_angle, start_node, radius, variance, points_per_leaf, graph: MultiDiGraph):
        #calculate where to put the start point in the circle
        start_point_index = self.planner.calculate_start_point_index(flower_angle, points_per_leaf)

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

    # Own algorithm here, flower idea
    def plan_circular_route_flower(self, start_coordinates, max_length: int, elevation_diff_input: int, options: dict) -> dict:

        """
        Generates a flower-like route structure on a given graph, where each leaf represents a circular path around the starting node.
        The algorithm places points on each petal, forming a route that connects them. The number of leafs, points per leaf, and other parameters can be adjusted.

        Parameters
        ----------
        - start_coordinates (tuple): The coordinates (latitude, longitude) of the starting point.
        - max_length (int): The maximum desired length of the generated route.
        - elevation_diff_input (int): The maximum desired elevation difference of the generated route.
        - options (dict): Additional options for analysis and visualization.

        Returns
        -------
        Output with all relative information for further analysis and visualization.

        Functionality
        -------------
        - Generates a circular pattern with a configurable number of leafs around the starting node.
        - Calculates the route by connecting points on each leaf.
        - Evaluates multiple paths and selects the one closest to the specified user input.
        - Performs path analysis, surface distribution analysis, and optionally visualizes the route.

        Note: This function is designed for route planning on a graph, considering geographical coordinates and various path attributes.

        Example Usage
        -------------
        start_coords = (latitude, longitude)
        max_route_length = 5000  # in meters
        analysis_options = {"analyze": True, "surface_dist": True}
        route_info = plan_circular_route_flower(start_coords, max_route_length, analysis_options)
        """
        print("flower route")
        #region Initial parameters and variables
        # Number of circles(leafs) drawn around start as flower
        leafs = 64
        # Number of points per leaf # TO DO!!!!: make this amount scale with the cicumference of the circle for precision
        points_per_leaf = 6
        
        # calculate the radius the circles(leafs) need to be
        radius = (max_length) / (2 * math.pi)
         # Has impact on the size of the circles(leafs)
        variance = 1
        additonal_variance = 1.1 #used for loading in a larger graph than necessary for more headroom additive to variance ALWAYS > 1
        
        # Load the graph
        graph = self.graph.full_geometry_point_graph(start_coordinates, radius = radius * (variance + additonal_variance)) #create a slightly larger map than necessary for more headroom
        
        # Determine the start node based on the start coordinates
        start_node = self.graph.closest_node(graph, start_coordinates) #this is the actual center_node( flower center node )
        print("Inputted route length: ", max_length)
        print("Inputted elevation difference: ", elevation_diff_input)
        #endregion

        #______________________________________________________________

        #region Calculate the leaf paths
        # Generate array of 360 equal sized angles, basically a circle, duhh
        flower_angles = np.linspace(0, 2 * np.pi, leafs)
        start_time_leafs = time.time()
        print(mp.cpu_count())

        # create list of multiple leaf path to evaluate LATER with multiprocessing
        with mp.Pool(mp.cpu_count()) as pool:
            func = partial(self.calculate_leaf_path, start_node=start_node, radius=radius, variance=variance, points_per_leaf=points_per_leaf, graph=graph)
            leaf_paths = pool.map(func, flower_angles)
        end_time_leafs = time.time()
        print("Time to calculate all leaf nodes: ", end_time_leafs - start_time_leafs)
        #endregion

        #______________________________________________________________

        # Visualize the leaf points
        self.visualizer.visualize_leaf_points(leaf_paths, graph)
        start_time = time.time()
        # Get all the full paths from the leafs with the lengths, indices match with eachother i.e. path_lengths[2] = paths[2]
        TRY TO MULTIPROCESS THIS
        paths, path_lengths = self.analyzer.get_paths_and_path_lengths(graph, leaf_paths)
        end_time = time.time()
        print("Time to calculate all FULL PATHS  ", end_time - start_time)
        min_length_diff_routes_indeces = self.analyzer.min_length_routes_indeces(paths, path_lengths, max_length, leafs)

        #______________________________________________________________

        # region get the best paths
        #TODO: IF there are more than length and height implemented in the future, you should work with scores, give each path a score and take the best one
        if elevation_diff_input != None:
            # Get the best matching path with elevation and length
            height_diffs = self.analyzer.get_height_diffs(graph, paths, path_lengths, min_length_diff_routes_indeces, elevation_diff_input) #calcualte difference betwen input and outcome of height values
            
            # get the path with the lowest elevation difference from the "amount" paths closest to the length input
            best_path_index = min(height_diffs, key=height_diffs.get)
            print("Best path: ", best_path_index)

            # set the path as the best path and display
            path = paths[best_path_index]

            #add start node to the end to make full circle
            path.append(start_node)
            self.visualizer.visualize_best_path(path, graph)

            # Get the path length of the best path
            path_length = path_lengths[best_path_index]
            elevation_diff = self.analyzer.calculate_elevation_diff(graph, path)
            # Visualize the elevation profile of the path with matplotlib
            self.visualizer.visualize_elevations(graph, path)
            print("path length (closest to input) meter: ", round(path_length))
            print("elevation difference: ", elevation_diff)

        elif elevation_diff_input == None:
            #only go for the best length
            path_length_diff = {}
            for path_index in min_length_diff_routes_indeces:
                temp_path_length = path_lengths[path_index]
                path_length_diff[path_index] = abs(temp_path_length - max_length)
            # get path matching the length input the best and show the elevation of the path
            best_path_index = min(path_length_diff, key=path_length_diff.get)
            print("Best path: ", best_path_index)
            path = paths[best_path_index]
            self.visualizer.visualize_best_path(path, graph)
            path_length = path_lengths[best_path_index]
            elevation_diff = self.analyzer.calculate_elevation_diff(graph, path)
            self.visualizer.visualize_elevations(graph, path)

        #endregion
        
        #______________________________________________________________

        #region Visualize the route

            # Visualize the route
        if "analyze" in options and options['analyze']:
            route_analysis = self.analyzer.get_path_attributes(graph, path)
        else:
            route_analysis = None

        if "surface_dist" in options and options['surface_dist']:
            surface_dist = self.analyzer.get_path_surface_distribution(route_analysis)
            surface_dist_visualisation = self.visualizer.build_surface_dist_visualisation(route_analysis, graph)

            surface_dist_legenda = {}
            for type in surface_dist:
                surface_dist_legenda[type] = (self.visualizer.get_surface_color(type))
        else:
            surface_dist = None
            surface_dist_visualisation = None
            surface_dist_legenda = None

        simple_polylines = self.visualizer.extract_polylines_from_folium_map(graph, path, invert=False)
        #endregion
        
        #______________________________________________________________

        output = {
            "start_node": start_node,
            "end_node": start_node,
            "path": path,
            "path_length": path_length,
            "route_analysis": route_analysis,
            "surface_dist": surface_dist,
            "surface_dist_visualisation": surface_dist_visualisation,
            "surface_dist_legenda": surface_dist_legenda,
            "simple_polylines": simple_polylines,
            "elevation_diff": elevation_diff
        }

        return output
    

    def normalize_coordinates(self, coordinates: str, delimiter: str = ",") -> Tuple:
            """Converts a front-end inputted coordinate string into a tuple of two floats.

            Args:
                coordinates (str): String of two delimited coordinates
                delimiter (str, optional): The delimiter. Defaults to ",".

            Returns:
                Tuple: (x.xx, y.yy) tuple of normalized coordinates.
            """

            return tuple([float(coordinate.strip()) for coordinate in coordinates.split(delimiter)])  
