from __future__ import annotations
from flask import Flask, render_template, request, jsonify
import folium
import json
from typing import Any, Optional
from heapq import heappop, heappush

app = Flask(__name__)

# ===== Custom Graph Classes =====

class _Vertex:
    item: Any
    neighbours: dict[_Vertex, tuple[int, list[Any]]]

    def __init__(self, item: Any, neighbours: dict[_Vertex, tuple[int, list[Any]]]) -> None:
        self.item = item
        self.neighbours = neighbours

    def __hash__(self): return hash(self.item)
    def __eq__(self, other): return isinstance(other, _Vertex) and self.item == other.item

    def check_connected(self, target_item: Any, visited: set[_Vertex]) -> bool:
        if self.item == target_item:
            return True
        visited.add(self)
        for u in self.neighbours:
            if u not in visited and u.check_connected(target_item, visited):
                return True
        return False

    def get_connected_component(self, visited: set[_Vertex]) -> set:
        if self in visited:
            return set()
        visited.add(self)
        connected_items = {self.item}
        for neighbour in self.neighbours:
            if neighbour not in visited:
                connected_items.update(neighbour.get_connected_component(visited))
        return connected_items

class Graph:
    _vertices: dict[Any, _Vertex]

    def __init__(self) -> None:
        self._vertices = {}

    def add_vertex(self, item: Any) -> None:
        self._vertices[item] = _Vertex(item, {})

    def add_edge(self, item1: Any, item2: Any, weight: int, path: Optional[list] = None) -> None:
        if item1 in self._vertices and item2 in self._vertices:
            v1, v2 = self._vertices[item1], self._vertices[item2]
            path = {} if not path else path
            v1.neighbours[v2] = (weight, path)
            v2.neighbours[v1] = (weight, path)
        else:
            raise ValueError

    def dijkstra_path(self, start: Any, end: Any) -> Optional[list[Any]]:
        if start not in self._vertices or end not in self._vertices:
            return None

        distances = {item: float('inf') for item in self._vertices}
        prev = {item: None for item in self._vertices}
        distances[start] = 0
        heap = [(0, start)]

        while heap:
            dist, current = heappop(heap)
            if current == end:
                break
            current_vertex = self._vertices[current]
            for neighbour in current_vertex.neighbours:
                cost = current_vertex.neighbours[neighbour][0]
                alt = dist + cost
                if alt < distances[neighbour.item]:
                    distances[neighbour.item] = alt
                    prev[neighbour.item] = current
                    heappush(heap, (alt, neighbour.item))

        path, node = [], end
        while node:
            path.insert(0, node)
            node = prev[node]
        return path if path and path[0] == start else None

    def greedy_tsp_with_adjacent_paths(self, start: Any, nodes: list[Any]) -> tuple[list[Any], int]:
        unvisited = set(nodes)
        full_path = [start]
        total_distance = 0
        unvisited.remove(start)
        current = start

        while unvisited:
            nearest = None
            nearest_dist = float('inf')
            nearest_path = []

            for candidate in unvisited:
                path = self.dijkstra_path(current, candidate)
                if path:
                    try:
                        dist = self.comp_path(path)
                        if dist < nearest_dist:
                            nearest = candidate
                            nearest_dist = dist
                            nearest_path = path
                    except:
                        continue

            if nearest is None:
                break

            if nearest_path[0] == full_path[-1]:
                nearest_path = nearest_path[1:]
            full_path += nearest_path
            total_distance += nearest_dist
            unvisited.remove(nearest)
            current = nearest

        return full_path, total_distance

    def connected(self, item1: Any, item2: Any) -> bool:
        if item1 in self._vertices and item2 in self._vertices:
            return self._vertices[item1].check_connected(item2, set())
        return False

    def comp_path(self, items: list) -> int:
        length = 0
        for i in range(len(items) - 1):
            v1 = self._vertices[items[i]]
            v2 = self._vertices[items[i + 1]]
            if v2 not in v1.neighbours:
                raise ValueError(f"{items[i]} and {items[i+1]} are not adjacent")
            length += v1.neighbours[v2][0]
        return length

    @property
    def vertices(self):
        return self._vertices


# ===== Load Graph from JSON =====

with open('graph_output.json', 'r') as f:
    graph_data = json.load(f)

nodes = graph_data['nodes']
graph = Graph()
markers = {}
TORONTO_LAT_MIN, TORONTO_LAT_MAX = 43.6, 43.7
TORONTO_LON_MIN, TORONTO_LON_MAX = -79.6, -79.3

for node in nodes:
    lat, lon = node.get('lat'), node.get('lng')
    name = node.get('name')
    if TORONTO_LAT_MIN <= lat <= TORONTO_LAT_MAX and TORONTO_LON_MIN <= lon <= TORONTO_LON_MAX:
        graph.add_vertex(name)
        markers[name] = (lat, lon)

for node in nodes:
    for edge in node.get("edges", []):
        f, t = node["name"], edge["neighbor"]
        if f in graph.vertices and t in graph.vertices:
            graph.add_edge(f, t, edge.get("distance", 1), edge.get("path", []))

# ===== Global State =====

last_path = []
last_result = {}

# ===== Flask Routes =====

@app.route('/')
def index():
    m = folium.Map(location=[43.65107, -79.38], zoom_start=12)

    # Add markers
    for label, coords in markers.items():
        popup_html = f"""
        <b>{label}</b><br>
        <button onclick="clickedMarkers.push('{label}'); document.getElementById('selection').innerHTML += '{label} → '; console.log(clickedMarkers);">Select</button>
        """
        popup = folium.Popup(popup_html, max_width=300)
        folium.Marker(location=coords, popup=popup, tooltip=label).add_to(m)

    # Draw the line if path exists
    if last_path:
        route_coords = [markers[n] for n in last_path if n in markers]
        if len(route_coords) >= 2:
            folium.PolyLine(route_coords, color="blue", weight=5, tooltip="Route").add_to(m)

    # Inject result message (if exists)
    result_html = ""
    if last_result:
        result_html = f"<b>Path:</b> {' → '.join(last_result['path'])}<br>" \
                      f"<b>Distance:</b> {last_result['distance']} m<br>" \
                      f"{last_result['message']}"

    # Inject JS + HTML UI
    js_code = f"""
    <div style="position:absolute; top:10px; left:10px; z-index:9999; background:white; padding:10px; border:1px solid #ccc; border-radius:5px;">
        <div id="selection"><b>Selected:</b> </div>
        <div id="result" style="margin-top:5px;">{result_html}</div>
        <button onclick="sendClickedNodes()">Calculate</button>
        <button onclick="clearSelection()">Clear</button>
    </div>

    <script>
        var clickedMarkers = [];

        function sendClickedNodes() {{
            fetch('/shortest_path', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ nodes: clickedMarkers }})
            }})
            .then(response => response.json())
            .then(data => {{
                window.location.reload();  // Force reload to draw path + show result
            }});
        }}

        function clearSelection() {{
            clickedMarkers = [];
            document.getElementById("selection").innerHTML = "<b>Selected:</b> ";
            document.getElementById("result").innerHTML = "";
        }}
    </script>
    """

    m.get_root().html.add_child(folium.Element(js_code))
    m.save("templates/map.html")
    return render_template("map.html")

@app.route('/shortest_path', methods=['POST'])
def shortest_path():
    global last_path, last_result
    data = request.get_json()
    selected = data.get("nodes", [])

    if len(selected) < 2:
        last_result = {"path": selected, "distance": 0, "message": "❗ Select at least 2 markers."}
        return jsonify(last_result)

    start = selected[0]
    tsp_path, distance = graph.greedy_tsp_with_adjacent_paths(start, selected)
    last_path = tsp_path
    last_result = {
        "path": tsp_path,
        "distance": round(distance, 2),
        "message": "✅ Greedy TSP path calculated."
    }
    return jsonify(last_result)

if __name__ == '__main__':
    app.run(debug=True)
