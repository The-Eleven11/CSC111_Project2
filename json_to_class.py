import json
from pj2_graph import Graph, _Vertex

def load_graph_from_json(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    graph = Graph()
    vertices = {}
    markers = {}

    # 为每个节点创建顶点，并提取坐标信息
    for node in data['nodes']:
        name = node['name']
        vertices[name] = _Vertex(item=name, neighbours={})
        markers[name] = [node['lat'], node['lng']]

    # 为每个节点添加边
    for node in data['nodes']:
        current = vertices[node['name']]
        for edge in node['edges']:
            neighbor_name = edge['neighbor']
            distance = edge['distance']
            current.neighbours[vertices[neighbor_name]] = (distance, [])

    # 将所有顶点加入图中
    for name, vertex in vertices.items():
        graph._vertices[name] = vertex
        print(graph._vertices[name])

    return graph, markers
