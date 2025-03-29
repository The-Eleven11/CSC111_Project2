import json
from pj2_graph import Graph, _Vertex

def load_graph_from_json(json_path: str) -> Graph:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    graph = Graph()

    vertices = {}
    for node in data['nodes']:
        name = node['name']
        vertices[name] = _Vertex(item=name, neighbours={})

    for node in data['nodes']:
        current = vertices[node['name']]
        for edge in node['edges']:
            neighbor_name = edge['neighbor']
            distance = edge['distance']
            current.neighbours[vertices[neighbor_name]] = (distance, [])

    for name, vertex in vertices.items():
        graph._vertices[name] = vertex

    return graph