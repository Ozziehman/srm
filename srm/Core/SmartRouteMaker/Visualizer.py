import json
import os
import osmnx as ox
import networkx as nx
from typing import Dict, List, OrderedDict
from networkx import MultiDiGraph
from matplotlib import pyplot as plt
import srtm

class Visualizer:

    def extract_polylines_from_folium_map(self, graph: MultiDiGraph, path: list, invert: bool = True, toJSObject: bool = True) -> List:
        """Extract the polylines from a folium map object.

        Args:
            graph (MultiDiGraph): Instance of an osmnx graph.
            path (list): Sequence of node ID's that form a path.
            invert (optional, bool): Invert coordinates for GeoJSON. Defaults to True.
            toJSObject (optional, bool): Convert the polylines to a jinja-renderable JS object. Defaults to True.

        Returns:
            List: [[[xxx, yyy], [xxx, yyy]], ...] List of coordinates that form a polyline.
        """        

        folium_map = ox.plot_route_folium(graph, path)

        polylines = []

        for child in folium_map._children:
            if str(child).startswith('poly_line_'):
                polylines.append(folium_map._children[child].locations)
        
        # Invert the coordinate sets to match the GeoJSON specification.
        # Normal: lat, long. GeoJSON: long, lat.
        if invert:
            for points in polylines:
                for coords in points:
                    coords.reverse()
        
        # Convert the coordinate list to a list of dictionaries.
        # This list can then be passed to Javascript using the |tojson jinja filter.
        if toJSObject:
            jsObject = []
            for line in polylines:
                jsObject.append({ "type": "LineString", "geometry": line })

            return jsObject
        
        return polylines
    
    def build_surface_dist_visualisation(self, analysedRoute: OrderedDict, graph: MultiDiGraph) -> Dict:
        """Builds a visualisation dictionary from a analysed route ordered dict.

        Args:
            analysedRoute (OrderedDict): Output ordered dict of the analyzer.

        Returns:
            Dict: Visualisation dictionary.
        """        

        with open('./srm/Core/SmartRouteMaker/config/VisualisationSettings.json', 'r') as settings:
            visualisationSettings = json.load(settings)

        visualisation = {}
        i = 1

        for edge in analysedRoute:
            visualisation[i] = {}
            visualisation[i]['osmid'] = edge['osmid']

            if "geometry" in edge:
                coordinates = []
                for coord in edge['geometry'].coords:
                    coordinates.append(list(coord))
                
                coordinates = []
                for coord in edge['geometry'].coords:
                    coordinates.append(list(coord))
                
                visualisation[i]['geometry'] = coordinates

                for coords in visualisation[i]['geometry']:
                    coords.reverse()
            else:
                visualisation[i]['geometry'] = 'missing'

            if "surface" in edge:
                if(type(edge['surface']) == list):
                    visualisation[i]['surface'] = edge['surface'][0]
                else:
                    visualisation[i]['surface'] = edge['surface']

                if visualisation[i]['surface'] in visualisationSettings['surfaces']:
                    visualisation[i]['targetColor'] = visualisationSettings['surfaces'][visualisation[i]['surface']]
                else:
                    visualisation[i]['targetColor'] = visualisationSettings['missing_surface']
            else:
                visualisation[i]['surface'] = 'unknown'
                visualisation[i]['targetColor'] = visualisationSettings['unknown_surface']
            
            i = i+1

        return visualisation

    def get_surface_color(self, surface: str) -> str:
        """Get the color a surface should be.

        Args:
            surface (str): Name of the surface.

        Returns:
            str: Hex value of the surface.
        """        

        with open('./srm/Core/SmartRouteMaker/config/VisualisationSettings.json', 'r') as settings:
            visualisationSettings = json.load(settings)

        return visualisationSettings['surfaces'][surface]
    
    def visualize_leaf_points(self, leaf_paths: list, graph: MultiDiGraph) -> None:
        """Visualize the leaf points and optionally save the plot as an image.

        Args
        ----------
        - leaf_paths (list): List of paths representing leaf nodes.
        - graph (MultiDiGraph): The graph containing node coordinates.
        - save_path (str, optional): Path to save the plot image. If None, the plot is not saved.

        Returns
        -------
        - None
        """
        save_path = "srm/Core/Static/Image/leaf_points.png"
        
        fig, ax = plt.subplots()

        for leaf_nodes in leaf_paths:
            # Extract x and y coordinates from leaf nodes
            leaf_x = [graph.nodes[node]["x"] for node in leaf_nodes]
            leaf_y = [graph.nodes[node]["y"] for node in leaf_nodes]

            # Plot the leaf path
            ax.plot(leaf_x, leaf_y, marker='o', linestyle=':')
        # Set labels and title
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title('All Points')

        if save_path:
            plt.savefig(save_path, format="png")

    def visualize_best_path(self, path: list, graph: MultiDiGraph) -> None:
        """Visualize the best path.

        Args
        ----------
        - path (list): List of paths representing leaf nodes.
        - graph (MultiDiGraph): The graph containing node coordinates.

        Returns
        -------
        - None
        """
        save_path = "srm/Core/Static/Image/best_path_points.png"
        
        fig, ax = plt.subplots()

        # Extract x and y coordinates from nodes
        leaf_x = [graph.nodes[node]["x"] for node in path]
        leaf_y = [graph.nodes[node]["y"] for node in path]

        # Plot the leaf path
        ax.plot(leaf_x, leaf_y, marker='o', linestyle=':')
        # Set labels and title
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title('Best path')

        if save_path:
            plt.savefig(save_path, format="png")

    def visualize_elevations(self, graph, path):
        """
        Visualize the elevations of a path and save the plot as an image.

        Parameters:
        graph (networkx.Graph): The graph representing the area.
        path (list): A list of node IDs representing the path.

        This method retrieves the elevation data for each node in the path using the SRTM library.
        It then creates a plot of the elevation data using matplotlib, with the node index on the x-axis and the elevation on the y-axis.
        The plot is saved as a PNG image at the specified save path.

        If there is an error retrieving the elevation data for a node, an error message is printed and the node is skipped.

        Note: The method uses the 'y' and 'x' attributes of the nodes in the graph to represent the latitude and longitude, respectively.
        """
        elevation_data = srtm.get_data()
        elevation_nodes = []
        plt.clf()
        for graphNode in path:
            node = graph.nodes[graphNode]
            nodeLat = node['y']
            nodeLon = node['x']

            try:
                elevation = elevation_data.get_elevation(nodeLat, nodeLon)
                elevation_nodes.append(elevation)
            except Exception as e:
                # Handle the case where getting elevation gioes wrong
                print(f"Error getting elevation for node {graphNode}: {e}")

        # Visualize elevation wit matplotlib
        save_path = "srm/Core/Static/Image/elevation.png"
        plt.plot(elevation_nodes, marker='.', linestyle='-', color='b')
        plt.title('Elevation Profile')
        plt.xlabel('Node Index')
        plt.ylabel('Elevation (meters)')
        plt.grid(True)
        if save_path:
            plt.savefig(save_path, format="png")

