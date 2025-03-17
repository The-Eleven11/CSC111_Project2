from __future__ import annotations
from flask import Flask, render_template, request, jsonify
import folium
from itertools import permutations
import json
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

    def dijkstra_path(self, start: Any, end: Any) -> Optional[list[Any]]:
        import heapq
        if start not in self._vertices or end not in self._vertices:
            return None

        distances = {item: float('inf') for item in self._vertices}
        prev = {item: None for item in self._vertices}
        distances[start] = 0
        heap = [(0, start)]

        while heap:
            dist, current = heapq.heappop(heap)
            if current == end:
                break
            current_vertex = self._vertices[current]
            for neighbour in current_vertex.neighbours:
                cost = current_vertex.neighbours[neighbour][0]
                alt = dist + cost
                if alt < distances[neighbour.item]:
                    distances[neighbour.item] = alt
                    prev[neighbour.item] = current
                    heapq.heappush(heap, (alt, neighbour.item))

        path = []
        node = end
        while node:
            path.insert(0, node)
            node = prev[node]

        return path if path and path[0] == start else None

    def greedy_tsp_with_adjacent_paths(self, start: Any, nodes: list[Any]) -> tuple[list[Any], int]:
        """Greedy TSP that includes intermediate adjacent paths when nodes aren't directly connected."""
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
                    dist = self.comp_path(path)
                    if dist < nearest_dist:
                        nearest = candidate
                        nearest_dist = dist
                        nearest_path = path

            if nearest is None:
                break  # no path to any remaining node

            # Add path (skip duplicate current node)
            if full_path and nearest_path[0] == full_path[-1]:
                nearest_path = nearest_path[1:]

            full_path += nearest_path
            total_distance += nearest_dist
            unvisited.remove(nearest)
            current = nearest

        return full_path, total_distance

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

# -------------------- Flask App --------------------

app = Flask(__name__)

# Load JSON data
with open('graph_output.json', 'r') as f:
    graph_data = json.load(f)

nodes = graph_data['nodes']
graph = Graph()
markers = {}

# Filter Toronto markers only
TORONTO_LAT_MIN, TORONTO_LAT_MAX = 43.6, 43.7
TORONTO_LON_MIN, TORONTO_LON_MAX = -79.6, -79.3

for node in nodes:
    lat, lon = node.get('lat'), node.get('lng')
    name = node.get('name')
    if TORONTO_LAT_MIN <= lat <= TORONTO_LAT_MAX and TORONTO_LON_MIN <= lon <= TORONTO_LON_MAX:
        graph.add_vertex(name)
        markers[name] = (lat, lon)

# Add edges from inside each node
edges = []
for node in nodes:
    for edge in node.get("edges", []):
        edges.append({
            "from": node["name"],
            "to": edge["neighbor"],
            "distance": edge.get("distance", 1),
            "path": []
        })

for edge in edges:
    f, t = edge["from"], edge["to"]
    if f in graph._vertices and t in graph._vertices:
        graph.add_edge(f, t, edge["distance"], edge["path"])


# -------------------- Routes --------------------

@app.route('/')
def index():
    m = folium.Map(location=[43.65107, -79.347015], zoom_start=13)

    for label, (lat, lon) in markers.items():
        popup_html = f"""
            <b>Marker: {label}</b><br>
            <button onclick="clickedMarkers.push('{label}'); document.getElementById('selection').innerHTML += '{label} '; console.log('Clicked:', clickedMarkers);">Add This Marker</button>
        """
        popup = folium.Popup(popup_html, max_width=250)
        folium.Marker([lat, lon], popup=popup, tooltip=label).add_to(m)

    js_code = """
        <div style="position:absolute; top:10px; left:10px; z-index:9999; background:white; padding:10px; border-radius:6px; border:1px solid #ccc; font-size:16px;">
            <div id="selection" style="margin-bottom:8px;"><b>Selected:</b> </div>
            <div id="result" style="margin-bottom:8px; color:green;"></div>
            <button onclick="sendClickedNodes()" style="margin-right:5px;">Calculate Path</button>
            <button onclick="clearSelection()">Clear</button>
        </div>
        <script>
            var clickedMarkers = [];

            function sendClickedNodes() {
                if (clickedMarkers.length < 2) {
                    document.getElementById("result").innerText = "Select at least 2 markers.";
                    return;
                }

                fetch('/shortest_path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ nodes: clickedMarkers })
                })
                .then(response => response.json())
                .then(data => {
                    const path = data.path.join(" → ");
                    const dist = data.distance;
                    const message = data.message || "";
                    document.getElementById("result").innerHTML =
                        "📍 <b>Path:</b> " + path + "<br>🧭 <b>Distance:</b> " + dist + " m<br>" + message;
                });
            }

            function clearSelection() {
                clickedMarkers = [];
                document.getElementById("selection").innerHTML = "<b>Selected:</b> ";
                document.getElementById("result").innerHTML = "";
            }
        </script>
    """
    m.get_root().html.add_child(folium.Element(js_code))
    m.save("templates/map.html")
    return render_template("map.html")


@app.route('/shortest_path', methods=['POST'])
def shortest_path():
    data = request.get_json()
    selected = data.get("nodes", [])

    if len(selected) < 2:
        return jsonify({"path": selected, "distance": 0, "message": "❗ Select at least 2 markers."})

    start = selected[0]
    tsp_path, distance = graph.greedy_tsp_with_adjacent_paths(start, selected)

    return jsonify({
        "path": tsp_path,
        "distance": round(distance, 2),
        "message": "✅ Greedy path with adjacent routing."
    })




if __name__ == '__main__':
    app.run(debug=True)
