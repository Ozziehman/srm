import osmnx as ox
import networkx as nx
from typing import OrderedDict
from networkx import MultiDiGraph

class Analyzer:

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