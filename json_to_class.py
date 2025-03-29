import json
from typing import Any
from pj2_graph import _Vertex

def load_graph_from_json(json_path: str) -> dict[str, _Vertex]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    name_to_vertex: dict[str, _Vertex] = {}
    for node in data['nodes']:
        v = _Vertex(item=node['name'])
        v.neighbours = {}
        name_to_vertex[node['name']] = v

    for node in data['nodes']:
        v = name_to_vertex[node['name']]
        for edge in node['edges']:
            neighbour_name = edge['neighbor']
            distance = edge['distance']
            neighbour_vertex = name_to_vertex.get(neighbour_name)
            if neighbour_vertex:
                v.neighbours[neighbour_vertex] = (distance, [])

    return name_to_vertex