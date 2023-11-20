import json
import osmnx as ox
import networkx as nx
from typing import Dict, List, OrderedDict
from networkx import MultiDiGraph

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
