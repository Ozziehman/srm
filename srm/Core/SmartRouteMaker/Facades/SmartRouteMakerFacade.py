import json
from turtle import st
from typing import Tuple
import osmnx as ox
import networkx as nx
import requests
import math
import numpy as np
import random

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


    # Own algorithm here, flower idea
    def plan_circular_route_flower(self, start_coordinates, max_length: int, options: dict) -> dict:

        """
        Generates a flower-like route structure on a given graph, where each petal represents a circular path around the starting node.
        The algorithm places points on each petal, forming a route that connects them. The number of petals, points per petal, and other parameters can be adjusted.

        Parameters
        ----------
        - start_coordinates (tuple): The coordinates (latitude, longitude) of the starting point.
        - max_length (int): The maximum desired length of the generated route.
        - options (dict): Additional options for analysis and visualization.

        Returns
        -------
        Output with all relavtive information for further analysis and visualization.

        Functionality
        -------------
        - Generates a circular pattern with a configurable number of leafs around the starting node.
        - Calculates the route by connecting points on each leaf.
        - Evaluates multiple paths and selects the one closest to the specified user input.
        - Performs path analysis, surface distribution analysis, and optionally visualizes the route.
        - Returns a comprehensive output dictionary with relevant information for further analysis and visualization.

        Note: This function is designed for route planning on a graph, considering geographical coordinates and various path attributes.

        Example Usage
        -------------
        start_coords = (latitude, longitude)
        max_route_length = 5000  # in meters
        analysis_options = {"analyze": True, "surface_dist": True}
        route_info = plan_circular_route_flower(start_coords, max_route_length, analysis_options)
        """
        print("flower route")
        
        # Number of circles(leafs) drawn around start as flower
        leafs = 32
        # Number of points per leaf # TO DO!!!!: make this amount scale with the cicumference of the circle for precision
        points_per_leaf = 5
        
        # calculate the radius the circles(leafs) need to be
        radius = (max_length) / (2 * math.pi)
         # Has impact on the size of the circles(leafs)
        variance = 1
        additonal_variance = 0 #used for loading in a larger graph than necessary for more headroom additive to vari
        
        # Load the graph
        graph = self.graph.full_geometry_point_graph(start_coordinates, radius = radius * (variance + additonal_variance)) #create a slightly larger map than necessary for more headroom
        
        # Determine the start node based on the start coordinates
        start_node = self.graph.closest_node(graph, start_coordinates) #this is the actual center_node( flower center node )
        print("Start: ", "(", graph.nodes[start_node]["x"], ",", graph.nodes[start_node]["y"], ")")
        print("Inputted route length: ", max_length)
        print("...........................................")
       

        # Generate array of 360 equal sized angles, basically a circle, duhh
        flower_angles = np.linspace(0, 2 * np.pi, leafs)

        # create list of multiple leaf path to evaluate LATER
        leaf_paths = []
        # directions: 0, 45, 90, 135, 180, 225, 270, 315 (E SE S SW W NW N NE) each direction generate a circle (EXAMPLE)
        for flower_angle in flower_angles:

            #calculate where to put the start point in the circle
            start_point_index = self.planner.calculate_start_point_index(flower_angle, points_per_leaf)
            
            #print("Unrounded start_point index: ", start_point_index)

            flower_direction = flower_angle

            #print("Flower direction: ",flower_direction)
            
            # Calculate the center of each leaf, based on the direction and the radius. Needs to be converted back to lon and lat, 111000 is the amount of meters in 1 degree of longitude/latitude
            difference_lon = math.cos(flower_direction) * radius * variance / 111000
            difference_lat = math.sin(flower_direction) * radius * variance / 111000
                  
            leaf_center_lon = float(graph.nodes[start_node]["x"]) + float(difference_lon)
            leaf_center_lat = float(graph.nodes[start_node]["y"]) + float(difference_lat)

            # Get the node closest to the center of the leaf
            leaf_center_node = self.graph.closest_node(graph, (leaf_center_lat, leaf_center_lon)) # lat = y, lon = x
            #test print
            #print("leaf_center: ", "(", graph.nodes[leaf_center_node]["x"], ",",  graph.nodes[leaf_center_node]["y"], ")")
            # generate leaf angles depending on the numbe of leafs to be generated
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

                # remove double nodes later on, but not right now to keep the start_index correct
                leaf_nodes.append(leaf_node)

            # Get the list in the correct order witht he correct nodes
            leaf_nodes = self.graph.insert_start_node_and_rearrange(leaf_nodes, start_node, start_point_index)
            leaf_paths.append(leaf_nodes)

            #test print
            for i in leaf_nodes:
                print("(", graph.nodes[i]["x"], ",",  graph.nodes[i]["y"], ")") 
            print("__________________________________________________________")


        # Area for making the actual path and adding it into the paths list for evaluation
        paths = []
        path_lengths = []
        #_________________________________________________________
        # Iterate thorugh all possible paths and choose the one closest to the input of the user
        
        for temp_path in leaf_paths:
            path = []
            temp_path_lengths = []
            # Loop through all shortest paths between the point and add them to 1 path (cyclus)
            for i in range(0, len(temp_path) - 1):
                j = i + 1
                if j >= len(temp_path):
                    j = 0
                try:
                    temp_path_lengths.append(self.analyzer.shortest_path_length(graph, temp_path[i], temp_path[j]))
                    for node in self.planner.shortest_path(graph, temp_path[i], temp_path[j]):
                        path.append(node)
                    # remove last node because the last in the final casce it adds the last and the last
                    path.pop(-1)
                    
                except nx.exception.NetworkXNoPath:
                    # No path error
                    print(f"No path from {temp_path[i]} to {temp_path[j]}")
                    continue

            if path != []:
                paths.append(path)
                path_lengths.append(sum(temp_path_lengths) * 1000)        

        min_length_diff_routes_indeces = self.analyzer.min_length_routes_indeces(paths, path_lengths, max_length, leafs)

        height_diffs = {}
        #testing var____
        elevation_diff_input = 100
        #_______________

        #calculate the elevation difference for each path and save it in a dict with the index of the path in the paths list as key
        for path_index in min_length_diff_routes_indeces:
            temp_path = paths[path_index]
            path_length = path_lengths[path_index]

            print("path length (closest to input) meter: ", path_length)

            # convert to km
            path_length /= 1000
            print("path length (closest to input) kilometer: ", path_length)

            # Get the sum of all upwards elevation changes in the all paths
            elevation_diff = self.analyzer.calculate_elevation_diff(graph, temp_path)
            print("elevation difference: ", elevation_diff)

            # enter the difference between the elevation difference of the path and the inputted elevation difference into a dict with the index 
            # of the path in the paths list as key, this does not take into account the start node twice(this is added later on)
            height_diffs[path_index] = abs(elevation_diff_input - elevation_diff)
            print("__________________________________________________________")
        print(height_diffs)

        # get the path with the lowest elevation difference from the "amount" paths closest to the length input
        best_path_index = min(height_diffs, key=height_diffs.get)
        print("Best path: ", best_path_index)

        # set the path as the best path and display
        path = paths[best_path_index]

        #add start node to the end to make full circle
        path.append(start_node)

        # Get the path length of the best path
        path_length = path_lengths[best_path_index]
        elevation_diff = self.analyzer.calculate_elevation_diff(graph, path)

        # calculate the total elevation of the path
        
        print(path)
        print("path length (closest to input) meter: ", path_length)
        print("elevation difference: ", elevation_diff)

        #_________________________________________________________

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
