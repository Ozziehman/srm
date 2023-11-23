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

        leafs = 8
        points_per_leaf = 3
        # Load the graph
        graph = self.graph.full_geometry_point_graph(start_coordinates)

        # Determine the start node based on the start coordinates
        start_node = self.graph.closest_node(graph, start_coordinates)

        # Has impact on the size of the circles(leafs)
        variance = 1

        # Generate array of 360 equal sized angles, basically a circle, duhh
        angle = np.linspace(0, 2 * np.pi, leafs)

        # create list of multiple leaf path to evaluate LATER
        leaf_paths = []
        # directions: 0, 45, 90, 135, 180, 225, 270, 315 (E SE S SW W NW N NE) each direction generate a circle
        for i in angle:
        #error:     direction = angle[i*(360/leafs)]  IndexError: only integers, slices (`:`), ellipsis (`...`), numpy.newaxis (`None`) and integer or boolean arrays are valid indices
            direction = i
          
            # Calculate how far to go in a direction according to the given length of the route
            radius = (max_length) / (2 * math.pi)

            # Calculate the center of each leaf, based on the direction and the radius. Needs to be converted back to lon and lat
            difference_lat = math.sin(direction) * radius * variance / 111000
            difference_lon = math.cos(direction) * radius * variance / 111000
            
            leaf_center_lat = float(graph.nodes[start_node]["x"]) + float(difference_lon)
            leaf_center_lon = float(graph.nodes[start_node]["y"]) + float(difference_lat)
            

            leaf_nodes = []

            # Get the node closest to the center of the leaf and place irt as the first int he path
            leaf_center_node = self.graph.closest_node(graph, (leaf_center_lat, leaf_center_lon)) # lat = y, lon = x
            if leaf_center_node not in leaf_nodes:
                leaf_nodes.append(leaf_center_node)
            
            # Generate the desired number of points on the circle and calculate the corresponding node
            angle = np.linspace(0, 2 * np.pi, points_per_leaf)

            # Create a circle around the current leaf_center_node, and create points on this leaf to make a route
            for i in angle:
                degree = i
                # Calculate the node on the circle(leaf) with lat and lon
                difference_lon = math.cos(degree) * radius / 111000
                difference_lat = math.sin(degree) * radius / 111000
                leaf_node_lat = float(graph.nodes[ leaf_center_node]["y"]) + float(difference_lat)
                leaf_node_lon = float(graph.nodes[ leaf_center_node]["x"]) + float(difference_lon)
                leaf_node = self.graph.closest_node(graph, (leaf_node_lat, leaf_node_lon))
                if leaf_node not in leaf_nodes:
                    leaf_nodes.append(leaf_node)
                

            # create empty leaf path to fill
            leaf_path = []
            # Create a path between the nodes on the leaf
            for i in range(len(leaf_nodes)-1):
                leaf_path.append(self.planner.shortest_path(graph, leaf_nodes[i], leaf_nodes[i+1]))
            
            leaf_paths.append(leaf_path)


        
        
        
    def normalize_coordinates(self, coordinates: str, delimiter: str = ",") -> Tuple:
            """Converts a front-end inputted coordinate string into a tuple of two floats.

            Args:
                coordinates (str): String of two delimited coordinates
                delimiter (str, optional): The delimiter. Defaults to ",".

            Returns:
                Tuple: (x.xx, y.yy) tuple of normalized coordinates.
            """

            return tuple([float(coordinate.strip()) for coordinate in coordinates.split(delimiter)])  
'''
    #Circular route
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



    