"""
project2: weighted graph
"""

from __future__ import annotations
from typing import Any, Optional


class _Vertex:
    """A vertex in a graph.

    Instance Attributes:
        - item: The data stored in this vertex.
        - neighbours: The vertices that are adjacent to this vertex.
            replace to a dictionary:
            key of dict is the neighbour _Vertex
            the value of dict is tuple of corresponding weight and list of _Vertex between these two _Vertex (empty for
                neighbour)

    Representation Invariants:
        - self not in self.neighbours
        - all(self in u.neighbours for u in self.neighbours)
    """
    item: Any
    neighbours: dict[_Vertex: tuple[int, list[Any]]]

    def __init__(self, item: Any, neighbours: dict[_Vertex: tuple[int, list[Any]]]) -> None:
        """Initialize a new vertex with the given item and neighbours."""
        self.item = item
        self.neighbours = neighbours

    # method to make this class hashable, so that it can be used in set and dict
    def __hash__(self):
        return hash(self.item)

    def __eq__(self, other):
        return isinstance(other, _Vertex) and self.item == other.item

    def check_connected(self, target_item: Any, visited: set[_Vertex]) -> bool:
        """Return whether this vertex is connected to a vertex corresponding to the target_item,
        WITHOUT using any of the vertices in visited.

        Preconditions:
            - self not in visited
        """
        if self.item == target_item:
            # Our base case: the target_item is the current vertex
            return True
        else:
            visited.add(self)  # Add self to the set of visited vertices
            for u in self.neighbours:
                if u not in visited:  # Only recurse on vertices that haven't been visited
                    if u.check_connected(target_item, visited):
                        return True
            return False

    def get_connected_component(self, visited: set[_Vertex]) -> set:
        """Return a set of all ITEMS connected to self by a path that does not use
        any vertices in visited.

        The items of the vertices in visited CANNOT appear in the returned set.

        Preconditions:
            - self not in visited

        Implementation notes:
            1. This can be implemented in a similar way to _Vertex.check_connected.
            2. This method must be recursive, and will have an implicit base case:
               when all vertices in self.neighbours are already in visited.
            3. Use a loop accumulator to store a set of the vertices connected to self.
        """
        # for loop version: not available since it is a method of _vertex, but it can be implemented if it is a method
        # of graph
        if self in visited:
            return set()  # If already visited, return an empty set

        visited.add(self)  # Mark this vertex as visited
        connected_items = {self.item}  # Store the item

        # Recursively explore unvisited neighbors
        for neighbour in self.neighbours:
            if neighbour not in visited:
                connected_items.update(neighbour.get_connected_component(visited))

        return connected_items

    def get_nearest_path_unvisited(self, visited: set) -> tuple:
        """
        to return the closest neighbour that is not in visited,
        a tuple (vertex.item, path)
        >>> g = Graph()
        >>> g.add_vertex('A')
        >>> g.add_vertex('B')
        >>> g.add_vertex('C')
        >>> g.add_edge('A', 'B', 2)
        >>> g.add_edge('A', 'C', 5)

        # unfinished test
        """
        nearest = float('inf')
        result = ()     # used for store vertex data
        for neighbour in self.neighbours:
            if self.neighbours[neighbour][0] < nearest and neighbour.item not in visited:
                nearest = self.neighbours[neighbour][0]
                result = neighbour, self.neighbours[neighbour][1]
        return result


class Graph:
    """A graph.

    Representation Invariants:
        - all(item == self._vertices[item].item for item in self._vertices)
    """
    # Private Instance Attributes:
    #     - _vertices:
    #         A collection of the vertices contained in this graph.
    #         Maps item to _Vertex object.
    _vertices: dict[Any, _Vertex]

    def __init__(self) -> None:
        """Initialize an empty graph (no vertices or edges)."""
        self._vertices = {}

    def add_vertex(self, item: Any) -> None:
        """Add a vertex with the given item to this graph.

        The new vertex is not adjacent to any other vertices.

        the neighbour is deflaut to be empty
        """
        self._vertices[item] = _Vertex(item, {})

    def add_edge(self, item1: Any, item2: Any, weight: int, path: Optional[list] = None) -> None:
        """Add an edge between the two vertices with the given items in this graph.

        Raise a ValueError if item1 or item2 do not appear as vertices in this graph.

        Preconditions:
            - item1 != item2
        """
        if item1 in self._vertices and item2 in self._vertices:
            v1 = self._vertices[item1]
            v2 = self._vertices[item2]

            # Add the new edge
            path = {} if not path else path
            v1.neighbours[v2] = (weight, path)
            v2.neighbours[v1] = (weight, path)
        else:
            # We didn't find an existing vertex for both items.
            raise ValueError

    def adjacent(self, item1: Any, item2: Any) -> bool:
        """Return whether item1 and item2 are adjacent vertices in this graph.

        Return False if item1 or item2 do not appear as vertices in this graph.
        """
        if item1 in self._vertices and item2 in self._vertices:
            v1 = self._vertices[item1]
            return any(v2.item == item2 for v2 in v1.neighbours)
        else:
            # We didn't find an existing vertex for both items.
            return False

    def get_neighbours(self, item: Any) -> set:
        """Return a set of the neighbours of the given item.

        Note that the *items* are returned, not the _Vertex objects themselves.

        Raise a ValueError if item does not appear as a vertex in this graph.
        """
        if item in self._vertices:
            v = self._vertices[item]
            return {neighbour.item for neighbour in v.neighbours}
        else:
            raise ValueError

    def degree(self, item: Any) -> int:
        """Return the degree of the vertex corresponding to the given item.

        Raise a ValueError if item does not appear as a vertex in this graph.

        >>> example_graph = Graph()
        >>> example_graph.add_vertex(10)
        >>> example_graph.add_vertex(20)
        >>> example_graph.add_vertex(30)
        >>> example_graph.add_edge(10, 20, 10)
        >>> example_graph.degree(10)
        1
        >>> example_graph.degree(30)
        0
        """
        if item not in self._vertices:
            raise ValueError
        return len(self._vertices[item].neighbours)

    def connected(self, item1: Any, item2: Any) -> bool:
        """Return whether item1 and item2 are connected vertices in this graph.

        Return False if item1 or item2 do not appear as vertices in this graph.

        >>> g = Graph()
        >>> g.add_vertex(1)
        >>> g.add_vertex(2)
        >>> g.add_vertex(3)
        >>> g.add_vertex(4)
        >>> g.add_edge(1, 2, 1)
        >>> g.add_edge(2, 3, 1)
        >>> g.connected(1, 3)
        True
        >>> g.connected(1, 4)
        False
        """
        if item1 in self._vertices and item2 in self._vertices:
            v1 = self._vertices[item1]
            return v1.check_connected(item2, set())  # Pass in an empty "visited" set
        else:
            return False

    def get_connected_component(self, item: Any) -> set:
        """Return a set of all ITEMS connected to the given item in this graph.

        Raise a ValueError if item does not appear as a vertex in this graph.

        >>> g = Graph()
        >>> for i in range(0, 5):
        ...     g.add_vertex(i)
        >>> g.add_edge(0, 1, 1)
        >>> g.add_edge(1, 2, 1)
        >>> g.add_edge(1, 3, 1)
        >>> g.add_edge(2, 3, 1)
        >>> g.get_connected_component(0) == {0, 1, 2, 3}
        True

        Note: we've implemented this method for you, and you should not change it.
        Instead, your task is to implement _Vertex.get_connected_component below.
        """
        if item not in self._vertices:
            raise ValueError
        else:
            return self._vertices[item].get_connected_component(set())

    def in_cycle(self, item: Any) -> bool:
        """Return whether the given item is in a cycle in this graph.

        Return False if item does not appear as a vertex in this graph.

        KEY OBSERVATION. A vertex v is in a cycle if and only if:
            v has two distinct neighbours u and w that are connected to each other
            by a path that doesn't use v.

        >>> g = Graph()
        >>> for i in range(0, 4):
        ...     g.add_vertex(i)
        >>> g.add_edge(0, 1, 1)
        >>> g.add_edge(1, 2, 1)
        >>> g.add_edge(1, 3, 1)
        >>> g.add_edge(2, 3, 1)
        >>> g.in_cycle(1)
        True
        >>> g.in_cycle(0)
        False

        Implementation notes:
            1. This method should call _Vertex.check_connected (following the above
               description).
            2. Don't try to make this method recursive, or copy and paste the implementation
               of _Vertex.check_connected! That's not necessary here.
        """
        if item not in self._vertices:
            return False
        else:
            # vertex should connect with two vertex, and these two vertex should connect to each other without
            # visiting vertex
            vertex = self._vertices[item]
            for neighbour1 in vertex.neighbours:
                for neighbour2 in vertex.neighbours:
                    if neighbour1.item != neighbour2.item and neighbour1.check_connected(neighbour2.item, {vertex}):
                        return True
            return False

    def comp_path(self, items: list) -> int:
        """
        compute the length of path stored in list, order matter
        return ValueError if any of nearby vertices are not adjacent
                >>> g = Graph()
        >>> for i in range(0, 4):
        ...     g.add_vertex(i)
        >>> g.add_edge(0, 1, 1)
        >>> g.add_edge(1, 2, 2)
        >>> g.add_edge(1, 3, 3)
        >>> g.add_edge(2, 3, 1)
        >>> g.comp_path([0, 1, 2, 3, 1])
        7
        """
        length_so_far = 0
        for i in range(len(items) - 1):
            if not self.connected(items[i], items[i + 1]):
                raise ValueError
            else:
                vertex1 = self._vertices[items[i]]
                vertex2 = self._vertices[items[i + 1]]
                part_length = vertex1.neighbours[vertex2][0]
                length_so_far += part_length
        return length_so_far

    # method 1
    """
    desecription: 
        always take the shortest way between two destinations
    exact steps:
        1. construct a complete graph, using dijkstra to construct the weight between two non-adjacent vertices
        2. take the smallest way to go
        3. stop until every destination is reached
    """

    def greedy_dijkstra(self, start: Any, targets: list[Any]) -> list:
        """
        input the graph firstly, and transform it as a complete graph, only targets are comprehensively to be passed
        path start at 'start'
        >>> g = Graph()
        >>> g.add_vertex('A')
        >>> g.add_vertex('B')
        >>> g.add_vertex('C')
        >>> g.add_vertex('D')
        >>> g.add_vertex('E')
        >>> g.add_vertex('F')
        >>> g.add_vertex('G')
        >>> g.add_edge('A', 'B', 2)
        >>> g.add_edge('A', 'C', 5)
        >>> g.add_edge('B', 'D', 1)
        >>> g.add_edge('B', 'E', 3)
        >>> g.add_edge('C', 'E', 2)
        >>> g.add_edge('C', 'F', 6)
        >>> g.add_edge('D', 'G', 4)
        >>> g.add_edge('E', 'G', 1)
        >>> g.add_edge('F', 'G', 3)
        >>> g.greedy_dijkstra('A', ['A', 'B', 'C'])
        ['A', 'B', 'E', 'C']
        >>> g.comp_path(g.greedy_dijkstra('A', ['A', 'B', 'C']))
        7

        >>> g2 = Graph()
        >>> g.add_vertex('A')
        >>> g.add_vertex('B')
        >>> g.add_vertex('C')
        >>> g.add_edge('A', 'B', 2)
        >>> g.add_edge('A', 'C', 5)
        >>> g.greedy_dijkstra('A', ['A', 'B', 'C'])
        ['A', 'B', 'A', 'C']
        >>> g.comp_path(g.greedy_dijkstra('A', ['A', 'B', 'C']))
        9
        """
        # using method to get the simplified complete graph based on targets
        simp_comp_graph = self.generate_complete_graph(targets)
        # start from the first vertex in simp_comp_graph, move to the nearest unreached vertex
        path = [start]
        visited = {start}
        start_point_vertex = simp_comp_graph._vertices[start]
        while not all(x in visited for x in targets):
            next_point, new_path = start_point_vertex.get_nearest_path_unvisited(visited)
            visited.add(next_point.item)
            path.extend(new_path)
            path.append(next_point.item)
            start_point_vertex = simp_comp_graph._vertices[next_point.item]
        return path

    def dijkstra(self, start: Any) -> dict:
        """
        to transform a graph into a dictionary about start to all other point's path
        Precondition:
        - start in graph
        # complex method
        >>> g = Graph()
        >>> g.add_vertex('A')
        >>> g.add_vertex('B')
        >>> g.add_vertex('C')
        >>> g.add_vertex('D')
        >>> g.add_vertex('E')
        >>> g.add_vertex('F')
        >>> g.add_vertex('G')

        # Adding edges with different weights
        >>> g.add_edge('A', 'B', 2)
        >>> g.add_edge('A', 'C', 5)
        >>> g.add_edge('B', 'D', 1)
        >>> g.add_edge('B', 'E', 3)
        >>> g.add_edge('C', 'E', 2)
        >>> g.add_edge('C', 'F', 6)
        >>> g.add_edge('D', 'G', 4)
        >>> g.add_edge('E', 'G', 1)
        >>> g.add_edge('F', 'G', 3)

        >>> shortest_paths = g.dijkstra('A')

        >>> shortest_paths['A']
        ['A']
        >>> shortest_paths['B']
        ['A', 'B']
        >>> shortest_paths['C']
        ['A', 'C']
        >>> shortest_paths['D']
        ['A', 'B', 'D']
        >>> shortest_paths['E']
        ['A', 'B', 'E']
        >>> shortest_paths['F']
        ['A', 'B', 'E', 'G', 'F']
        >>> shortest_paths['G']
        ['A', 'B', 'E', 'G']
        >>> g.comp_path(shortest_paths['G'])
        6
        """
        if start not in self._vertices:
            raise ValueError("Start vertex not found in graph.")

        # Step 1: Initialize distances and previous nodes
        shortest_distances = {vertex: float('inf') for vertex in self._vertices}
        previous_nodes = {vertex: None for vertex in self._vertices}
        shortest_distances[start] = 0

        # Set of unvisited nodes
        unvisited = set(self._vertices.keys())

        while unvisited:
            # Select the vertex with the smallest known distance
            current = min(unvisited, key=lambda vertex: shortest_distances[vertex])

            # If the smallest distance is still infinity, break (remaining nodes are unreachable)
            if shortest_distances[current] == float('inf'):
                break

            # Process each neighbor of the current vertex
            for neighbor, (weight, _) in self._vertices[current].neighbours.items():
                new_distance = shortest_distances[current] + weight
                if new_distance < shortest_distances[neighbor.item]:
                    shortest_distances[neighbor.item] = new_distance
                    previous_nodes[neighbor.item] = current  # Track path

            # Mark the node as visited
            unvisited.remove(current)

        # Step 2: Build paths dictionary
        paths = {}
        for destination in self._vertices:
            path = []
            current = destination
            while current is not None:
                path.append(current)
                current = previous_nodes[current]
            path.reverse()
            paths[destination] = path if path[0] == start else None  # Ensure valid path

        return paths

    def simplify_dijkstra(self, targets: list[Any], paths: dict) -> dict:
        """
        to return a dict that only contains the target vertices that are required to be reached
        target is the name of destination (Any), input the target destination and result of dijkstra
        >>> g = Graph()
        >>> g.add_vertex('A')
        >>> g.add_vertex('B')
        >>> g.add_vertex('C')
        >>> g.add_vertex('D')
        >>> g.add_vertex('E')
        >>> g.add_vertex('F')
        >>> g.add_vertex('G')
        >>> g.add_edge('A', 'B', 2)
        >>> g.add_edge('A', 'C', 5)
        >>> g.add_edge('B', 'D', 1)
        >>> g.add_edge('B', 'E', 3)
        >>> g.add_edge('C', 'E', 2)
        >>> g.add_edge('C', 'F', 6)
        >>> g.add_edge('D', 'G', 4)
        >>> g.add_edge('E', 'G', 1)
        >>> g.add_edge('F', 'G', 3)
        >>> target_paths = g.simplify_dijkstra(['A', 'B', 'G'], g.dijkstra('A'))
        >>> target_paths['A']
        ['A']
        >>> target_paths['B']
        ['A', 'B']
        >>> target_paths['G']
        ['A', 'B', 'E', 'G']

        # >>> target_paths['C']
        # KeyError
        """
        new_paths = {}
        for path in paths:
            if path in targets:
                new_paths[path] = paths[path]
        return new_paths

    def generate_complete_graph(self, targets: list[Any]) -> Graph:
        """
        return a new complete graph, according to paths input
        (dict of dijkstra graph {item: its paths to other targets})
        >>> g = Graph()
        >>> g.add_vertex('A')
        >>> g.add_vertex('B')
        >>> g.add_vertex('C')
        >>> g.add_vertex('D')
        >>> g.add_vertex('E')
        >>> g.add_vertex('F')
        >>> g.add_vertex('G')
        >>> g.add_edge('A', 'B', 2)
        >>> g.add_edge('A', 'C', 5)
        >>> g.add_edge('B', 'D', 1)
        >>> g.add_edge('B', 'E', 3)
        >>> g.add_edge('C', 'E', 2)
        >>> g.add_edge('C', 'F', 6)
        >>> g.add_edge('D', 'G', 4)
        >>> g.add_edge('E', 'G', 1)
        >>> g.add_edge('F', 'G', 3)
        >>> g_g = g.generate_complete_graph(['A', 'B', 'G'])
        >>> g_g.adjacent('A', 'G')
        True
        >>> g_g.adjacent('B', 'G')
        True
        >>> g_g.degree('A')
        2
        >>> g_g.get_neighbours('A')
        {'B', 'G'}
        """
        paths = {item: self.simplify_dijkstra(targets, self.dijkstra(item)) for item in targets}
        g = Graph()
        # firstly add all vertices
        for item in paths:
            g.add_vertex(item)
        # secondly add all edges
        for item in paths:
            for target in paths[item]:
                if target != item:
                    g.add_edge(item, target, self.comp_path(paths[item][target]), paths[item][target][1: -1])
        return g

    # method 2
    """
    desecription: 
        always move to point that the rest path is the shortest
    exact steps:
        1. construct a complete graph, using dijkstra to construct the weight between two non-adjacent vertices
        2. compute the sum of result path for all other unvisitied vertices, if move to the nearby vertices,
        3. move the the lowest sum vertex
        4. stop until every destination is reached
    """
