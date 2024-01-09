import time
from typing import Tuple
import math
import numpy as np
import multiprocessing as mp
from networkx import MultiDiGraph
from functools import partial
from termcolor import colored
import colorama

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
        self.visualizer.visualize_best_path(path, graph)
        

        elevation_nodes = self.analyzer.calculate_elevation_diff(graph, path)
        self.visualizer.visualize_elevations(graph, path)


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

    

    # Own algorithm here, flower idea
    def plan_circular_route_flower(self, start_coordinates, max_length: int, elevation_diff_input: int, percentage_hard_input:int, options: dict) -> dict:

        """
        Generates a flower-like route structure on a given graph, where each leaf represents a circular path passing the 
        starting node. The algorithm places points on each leaf, forming a route that connects them. The number of leafs, 
        points per leaf, and other parameters can be adjusted.

        Parameters
        ----------
        start_coordinates : tuple
            The coordinates (latitude, longitude) of the starting point.
        max_length : int
            The maximum desired length of the generated route.
        elevation_diff_input : int
            The maximum desired elevation difference of the generated route.
        percentage_hard_input : int
            The maximum desired percentage of hardened surfaces of the generated route.
        options : dict
            Additional options for analysis and visualization.

        Returns
        -------
        dict
            Output with all relative information for further analysis and visualization.

        Notes
        -----
        - Generates a circular pattern with a configurable number of leafs around the starting node.
        - Calculates the route by connecting points on each leaf.
        - Evaluates multiple paths and selects the one closest to the specified user input.
        - Performs path analysis, surface distribution analysis, and optionally visualizes the route.
        - This function is designed for route planning on a graph, considering geographical coordinates and various path attributes.

        Example
        -------
        >>> start_coordinates = (latitude, longitude)
        >>> max_length = the input from the user in meters
        >>> elevation_diff_input = the input from the user in meters
        >>> percentage_hard_input = the input from the user in percentage
        >>> options = {"analyze": True, "surface_dist": True}
        """
        colorama.init()
        start_time_full = time.time()
        print(f"Route from point {start_coordinates}")
        #region Initial parameters and variables

        # Number of circles(leafs) drawn around start as flower
        leafs = 64
        points_per_leaf = 5
        
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
        print("Inputted percentage hardened: ", percentage_hard_input)
        #endregion

        #______________________________________________________________

        #region Calculate the leaf paths
        # Generate array of 360 equal sized angles, basically a circle, duhh
        flower_angles = np.linspace(0, 2 * np.pi, leafs)
        start_time_leafs = time.time()
        print("spreading load over: ", mp.cpu_count(), " cores")

        # create list of multiple leaf paths to evaluate LATER with multiprocessing
        with mp.Pool(mp.cpu_count()) as pool:
            func = partial(self.planner.calculate_leaf_nodes, start_node=start_node, radius=radius, variance=variance, points_per_leaf=points_per_leaf, graph=graph)
            leaf_paths = pool.map(func, flower_angles)
        end_time_leafs = time.time()
        print("Time to calculate all leaf nodes: ", end_time_leafs - start_time_leafs)
        #endregion

        #______________________________________________________________

        # Visualize the leaf points
        self.visualizer.visualize_leaf_points(leaf_paths, graph)
        start_time = time.time()
        
        # region get all the full paths from the leafs
        # Get all the full paths from the leafs with the lengths, indices match with eachother i.e. path_lengths[2] = paths[2]
        paths, path_lengths = self.analyzer.get_paths_and_path_lengths(graph, leaf_paths, start_node)


        print(colored("total_paths: ", "yellow"), len(paths))
        #remove faulty routes, first collect the valid paths and then remove the faulty ones from the original lists to avoid runtime errors:
        
        valid_paths = []
        valid_path_lengths = []
        for path in paths:
            try:
                self.analyzer.get_path_attributes(graph, path)
                valid_paths.append(path)
                valid_path_lengths.append(path_lengths[paths.index(path)])
            except:
                print(colored("removed faulty path, index: ", "red"), paths.index(path))
                
        paths = valid_paths
        path_lengths = valid_path_lengths
       
        print(colored("valid_paths: ","green"), len(paths))

        
        end_time = time.time()
        print("Time to calculate all FULL PATHS  ", end_time - start_time)
        #endregion
        min_length_diff_routes_indeces = self.analyzer.min_length_routes_indeces(paths, path_lengths, max_length, leafs)
        
        #______________________________________________________________

        # region get the best paths
        #TODO: Clean this mess a bit up, it works but its not pretty

        if elevation_diff_input != None or percentage_hard_input != None:
            
            # Get the best matching path with elevation and length
            paths_with_scores = {}

            # only length and elevation
            
            if elevation_diff_input != None and percentage_hard_input == None:
                paths_with_scores = self.analyzer.get_score_only_elevation(graph, paths, path_lengths, min_length_diff_routes_indeces, elevation_diff_input, max_length)

            # only length and surface
            elif percentage_hard_input != None and elevation_diff_input == None:
                paths_with_scores = self.analyzer.get_score_only_surface(graph, paths, path_lengths, min_length_diff_routes_indeces, percentage_hard_input, max_length)

            # both length, elevation and surface
            elif elevation_diff_input != None and percentage_hard_input != None:
                paths_with_scores = self.analyzer.get_score_elevation_and_surface(graph, paths, path_lengths, min_length_diff_routes_indeces, percentage_hard_input, elevation_diff_input, max_length)
            
           # get path with the lowest score, this is the best path (the score is the difference between input and output, so the lower the better)
            best_path_index = min(paths_with_scores, key=paths_with_scores.get)
            print("Best path: ", best_path_index)

            # set the path as the best path
            path = paths[best_path_index]

            self.visualizer.visualize_best_path(path, graph)

            # results
            #return these results in seperate function
            path_length = round(path_lengths[best_path_index],2)
            elevation_diff = self.analyzer.calculate_elevation_diff(graph, path)
            percentage_hardened = self.analyzer.calculate_percentage_hardened_surfaces(graph, path, path_length)

            self.visualizer.visualize_surface_percentage(percentage_hardened)
            self.visualizer.visualize_elevations(graph, path)
            
            # terminal message
            self.visualizer.final_terminal_message(path_length, elevation_diff, percentage_hardened)
#___________________________________________________________________________________________________________________

        # only length
        elif elevation_diff_input == None and percentage_hard_input == None:
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

            #results
            #return these results in seperate function
            path_length = round(path_lengths[best_path_index],2)
            elevation_diff = self.analyzer.calculate_elevation_diff(graph, path)
            percentage_hardened = self.analyzer.calculate_percentage_hardened_surfaces(graph, path, path_length)


            self.visualizer.visualize_surface_percentage(percentage_hardened)
            self.visualizer.visualize_elevations(graph, path)
            
            
            # terminal message
            self.visualizer.final_terminal_message(path_length, elevation_diff, percentage_hardened)
        #endregion
        
        #______________________________________________________________
        end_time_full = time.time()
        print("Total time: ", end_time_full - start_time_full)
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
    
    def export_GPX(self, node_ids: list):
        return self.graph.export_GPX(node_ids)
    

    def normalize_coordinates(self, coordinates: str, delimiter: str = ",") -> Tuple:
            """Converts a front-end inputted coordinate string into a tuple of two floats.

            Args:
                coordinates (str): String of two delimited coordinates
                delimiter (str, optional): The delimiter. Defaults to ",".

            Returns:
                Tuple: (x.xx, y.yy) tuple of normalized coordinates.
            """

            return tuple([float(coordinate.strip()) for coordinate in coordinates.split(delimiter)])  
