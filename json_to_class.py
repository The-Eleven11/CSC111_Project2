import json
from pj2_graph import Graph, _Vertex

def load_graph_from_json(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    graph = Graph()
    markers = {}

    for node in data['nodes']:
        name = node['name']
        graph.add_vertex(name)
        markers[name] = [node['lat'], node['lng']]

    for node in data['nodes']:
        current = node['name']
        for edge in node['edges']:
            graph.add_edge(current, edge['neighbor'], edge['duration'])

    return graph, markers