"""
    this is the file that use to implement the algorithm related to graph
"""
from typing import Any
import pj2_graph


def greedy_dijkstra_method1(graph: pj2_graph.Graph, start: Any, destination: list[Any]) -> list:
    """
    method 1 as describe in pj2_graph
    """
    return graph.greedy_dijkstra(start, destination)

# method 2
#
#
# """
# desecription:
#     always move to point that the rest path is the shortest
# exact steps:
#     1. construct a complete graph, using dijkstra to construct the weight between two non-adjacent vertices
#     2. compute the sum of result path for all other unvisitied vertices, if move to the nearby vertices,
#     3. move the the lowest sum vertex
#     4. stop until every destination is reached
# """
#
#
def greedy_dijkstra_method2(graph: pj2_graph.Graph, start: Any, destination: list[Any]) -> list:
    """
    as shown above
    """
    simp_comp_graph = graph.generate_complete_graph(destination)
    path = [start]
    visited = {start}
    start_point_vertex = simp_comp_graph.get_Vertex(start)
    while not all(x in visited for x in destination):
        next_point, new_path = start_point_vertex.get_nearest_path_unvisited(visited)
        curr_sum = float('inf')
        for neighbour in graph.get_neighbours(start):
            sum_so_far = sum([neighbour.neighbours[x][0] for x in graph.get_neighbours(neighbour) if x not in visited])
            if sum_so_far < curr_sum:
                next_point = neighbour
                new_path = start_point_vertex.neighbours[next_point][1]
        visited.add(next_point.item)
        path.extend(new_path)
        path.append(next_point.item)
        start_point_vertex = simp_comp_graph.get_Vertex(next_point.item)
    return path
