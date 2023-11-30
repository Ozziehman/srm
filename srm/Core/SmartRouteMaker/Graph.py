import osmnx as ox
from networkx import MultiDiGraph

class Graph:

    def simple_point_graph(self, coordinates: tuple, radius: int = 5000, type: str = "bike") -> MultiDiGraph:
        """Creates a MultiDiGraph from a set of coordinates and a radius.

        Args:
            coordinates (tuple): Coordinates that should be the center of the graph.
            radius (int, optional): Radius around the center that should be downloaded. Defaults to 5000.
            type (str, optional): Type of road network. Defaults to "bike".

        Returns:
            MultiDiGraph: Instance of an osmnx graph.
        """

        ox.settings.useful_tags_way = [
            'bridge', 'tunnel', 'oneway', 'lanes', 'ref', 'name',
            'highway', 'maxspeed', 'service', 'access', 'area',
            'landuse', 'width', 'est_width', 'surface', 'junction',
            'lon', 'lat'
        ]

        return ox.graph_from_point(coordinates, radius, network_type=type)
    
    def full_geometry_point_graph(self, coordinates: tuple, radius: int = 5000, type: str = "bike") -> MultiDiGraph:
        """Creates a MultiDiGraph that contains all geometry attributes from a set of coordinates and a radius.

        Args:
            coordinates (tuple): Coordinates that should be the center of the graph.
            radius (int, optional): Radius around the center that should be downloaded. Defaults to 5000.
            type (str, optional): Type of road network. Defaults to "bike".

        Returns:
            MultiDiGraph: Instance of an osmnx graph.
        """        

        ox.settings.useful_tags_way = [
            'bridge', 'tunnel', 'oneway', 'lanes', 'ref', 'name',
            'highway', 'maxspeed', 'service', 'access', 'area',
            'landuse', 'width', 'est_width', 'surface', 'junction',
            'lon', 'lat'
        ]

        # Download graph and convert to nodes and edges
        graph = ox.graph_from_point(coordinates, radius, network_type=type)
        nodes, edges = ox.graph_to_gdfs(graph, fill_edge_geometry=True)
        
        return ox.graph_from_gdfs(nodes, edges, graph_attrs=graph.graph)

    def closest_node(self, graph: MultiDiGraph, coordinates: tuple) -> int:
        """Fetches the closest node to a set of coordinates within a graph.

        Args:
            graph (MultiDiGraph): Instance of an osmnx graph.
            coordinates (tuple): Coordinates that the node should be close to.

        Returns:
            int: Unique ID of the closest node in the graph.
        """

        return ox.nearest_nodes(graph, coordinates[1], coordinates[0])     
        # return ox.nearest_nodes(graph, longtitude(x), latitude(y))   

    def insert_start_node_and_rearrange(self, leaf_nodes, start_node, start_point_index):
            leaf_nodes.insert(int(round(start_point_index)), start_node)

            # transform list into right order so the start point is in the front
            front_part = leaf_nodes[int(round(start_point_index)):]
            back_part = leaf_nodes[:int(round(start_point_index))]

            # put the list back together
            leaf_nodes = front_part + back_part

            # take out the duplicates
            leaf_nodes = list(dict.fromkeys(leaf_nodes))

            # add the start node to the end of the list to make a full circle
            leaf_nodes.append(start_node)

            return leaf_nodes


