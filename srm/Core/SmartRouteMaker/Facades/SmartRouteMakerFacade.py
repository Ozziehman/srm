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

        """Generates a flower like structure on a given graph with circles
        which centers are N NE NW S SE SW E W of the starting node. On each circle the algorithm
        places 4 (or more, depending on future ideas) point which are used for making a route."""
        print("flower route")
        
        # Number of circles(leafs) drawn around start as flower
        leafs = 24
        # Number of points per leaf # TO DO!!!!: make this amount scale with the cicumference of the circle for precision
        points_per_leaf = 8
        
        # calculate the radius the circles(leafs) need to be
        radius = (max_length) / (2 * math.pi)
         # Has impact on the size of the circles(leafs)
        variance = 1
        additonal_radius = 3 #used for loading in a larger graph than necessary for more headroom
        
        # Load the graph
        graph = self.graph.full_geometry_point_graph(start_coordinates, radius = radius * (variance + additonal_radius)) #create a slightly larger map than necessary for more headroom
        
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

            # Calculate the index of the start point on the circle, based on the direction of the circle
            start_point_index = ((flower_angle * (180 / math.pi))/360) * points_per_leaf + (points_per_leaf/2)
            if start_point_index >= points_per_leaf:
                start_point_index = start_point_index - points_per_leaf
            #test print
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

            leaf_nodes.insert(int(round(start_point_index)), start_node)
            # transform list into right order so the start point is in the front
            front_part = leaf_nodes[int(round(start_point_index)):]
            back_part = leaf_nodes[:int(round(start_point_index))]
            leaf_nodes = front_part + back_part
            # take out the duplicates
            leaf_nodes = list(dict.fromkeys(leaf_nodes))
            # add the gathered leaf nodes to the leaf_paths list and repeat loop for next leaf   
            leaf_paths.append(leaf_nodes) # will end up with 1 extra node, that is the starting node

            #test print
            #for i in leaf_nodes:
            #    print("(", graph.nodes[i]["x"], ",",  graph.nodes[i]["y"], ")") 
            #print("__________________________________________________________")


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
                    # remove last node because the last in the final casce it adds the last and the last _______________NOT GOOD??????____________________
                    path.pop(-1)
                    
                except nx.exception.NetworkXNoPath:
                    # No path error
                    print(f"No path from {temp_path[i]} to {temp_path[j]}")
                    continue

            if path != []:
                paths.append(path)
                path_lengths.append(sum(temp_path_lengths) * 1000)        

        path = []
        path_length = 0
        path_length_diff = {}
        # find the path closest to the input of the user
        for i in range(0, len(paths)):
            path_length_diff[i] = abs(path_lengths[i] - max_length)
        #print(path_length_diff)

       
        
        # find the index of the path with the smallest difference
        min_diff = min(path_length_diff.values())
        min_diff_index = list(path_length_diff.keys())[list(path_length_diff.values()).index(min_diff)]
        path = paths[min_diff_index]
        path_length = path_lengths[min_diff_index]
        print("path length (closest to input) meter: ", path_length)
        # convert to km
        path_length /= 1000
        print("path length (closest to input) kilometer: ", path_length)

        #_________________________________________________________

        elevation_nodes = self.analyzer.calculate_elevation_diff(graph, path)

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
            "elevation_nodes": elevation_nodes
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

    '''#Circular route
    def plan_circular_route(self, start_coordinates, max_length: int, options: dict) -> dict:
        """Generates a circular path on a given graph, 
        starting from a specified set of coordinates. 
        The algorithm utilizes geometric calculations to determine the direction 
        and distance of points on the circle around the starting node. 
        The circular path is created by selecting a certain number of points on the circle, 
        and the algorithm calculates the corresponding nodes on the graph.
        """

        # Number of points on the circle
        i_points = 10

        # Load the data
        graph = self.graph.full_geometry_point_graph(start_coordinates)

        # Determine the start node based on the start coordinates
        start_node = self.graph.closest_node(graph, start_coordinates)

        variance = 1

        # Provide 360 possible directions, choose a direction
        angle = np.linspace(0, 2 * np.pi, 360)
        direction = angle[random.randint(0, 359)]

        # Calculate how far to go in a direction according to the given length of the route
        radius = max_length / math.pi / 2

        # Convert the radius back to longitude and latitude, choose the center of the circle
        difference_lon = math.cos(direction) * radius * variance / 111000
        difference_lat = math.sin(direction) * radius * variance / 111000
        x = float(graph.nodes[start_node]["x"]) + float(difference_lon)
        y = float(graph.nodes[start_node]["y"]) + float(difference_lat)

        center = ox.nearest_nodes(graph, x, y)

        circle_dpoints = i_points

        # Create variables to store data and nodes
        points_data = dict()
        points = []

        # Generate the desired number of points on the circle and calculate the corresponding node
        angle = np.linspace(0, 2 * np.pi, circle_dpoints)
        for i in angle:
            degree = i
            difference_lon = math.cos(degree) * radius / 111000
            difference_lat = math.sin(degree) * radius / 111000
            y = float(graph.nodes[center]["y"]) + float(difference_lat)
            x = float(graph.nodes[center]["x"]) + float(difference_lon)
            circle_node = ox.nearest_nodes(graph, x, y)

            points_data[circle_node] = graph.nodes[circle_node]
            points.append(circle_node)

        # Calculate the route between the previously selected points
        cyclus = []
        # Loop through all shortest paths between the point and add them to 1 path (cyclus)
        for i in range(0, len(points) - 1):
            j = i + 1
            if j >= len(points):
                j = 0
            for node in self.planner.shortest_path(graph, points[i], points[j]):
                cyclus.append(node)
            #remove last node because the last 2 nodes are the same
            cyclus.pop(-1)

        path = cyclus

        #test print
        #for x in path:
        #    print(x)

        elevation_nodes = self.analyzer.calculate_elevation_diff(graph, path)

        path_length = 999999
       

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
            "elevation_nodes": elevation_nodes
        }

        return output
'''



    