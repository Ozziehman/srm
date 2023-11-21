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
        
        elevation_nodes = []

        #Getting the elevation of the nodes in the path
        for graphNode in path:
            node = graph.nodes[graphNode]
            nodeLat = node['y']
            nodeLon = node['x']
            api_url = f"https://api.open-meteo.com/v1/elevation?latitude={nodeLat}&longitude={nodeLon}"

            # Make the API call
            response = requests.get(api_url)

            # Check if the request was successful
            if response.status_code == 200:
                elevation_nodes.append(response.json())
            else:
                print(f"Error making API call to {api_url}. Status code: {response.status_code}")
        for i in elevation_nodes:
            print(i)

        # this is a collection of all the nodes that are in the route (including the start and end node) turn these nodes into coordinates
        # to get the lat & lon of the node, this can be used in an API for example: https://open-meteo.com/en/docs/elevation-api

        # Right now im thinking of generating 3-5 different routes and then picking the one with the closest elevation difference to the inputted elevation difference
        # It is pretty impossible and unlikely to get the exact elevation with the exact distance and vice versa. So we need to find a balance between the two.

        # Begin with getting the elevation after generating the routes.

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




    #Circular route
    def plan_circuit(self, start_coordinates, options: dict, max_length: int) -> dict:
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

        variance = 0.9

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
            cirkel_node = ox.nearest_nodes(graph, x, y)

            points_data[cirkel_node] = graph.nodes[cirkel_node]
            points.append(cirkel_node)

        # Calculate the route between the previously selected points
        cyclus = []
        # Loop through all shortest paths between the point and add them to 1 path (cyclus)
        for i in range(0, len(points) - 1):
            j = i + 1
            if j >= len(points):
                j = 0
            for node in self.planner.shortest_path(graph, points[i], points[j]):
                cyclus.append(node)

            cyclus.pop(-1)

        path = cyclus

        #test print
        for x in path:
            print(x)

        elevation_nodes = []

        #Getting the elevation of the nodes in the path
        for graphNode in path:
            node = graph.nodes[graphNode]
            nodeLat = node['y']
            nodeLon = node['x']
            api_url = f"https://api.open-meteo.com/v1/elevation?latitude={nodeLat}&longitude={nodeLon}"

            # Make the API call
            response = requests.get(api_url)

            # Check if the request was successful
            if response.status_code == 200:
                elevation_nodes.append(response.json())
            else:
                print(f"Error making API call to {api_url}. Status code: {response.status_code}")
        for i in elevation_nodes:
            print(i)

        path_length = self.analyzer.calculate_path_length(graph, path)

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
            "simple_polylines": simple_polylines
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