from flask import Flask, render_template, request, jsonify
import folium
from json_to_class import load_graph_from_json
from pj2_graph_alg import greedy_dijkstra_method1

app = Flask(__name__)

# ===== Load Graph from JSON and External Files =====
graph = load_graph_from_json("graph_output.json")
markers = {}
TORONTO_LAT_MIN, TORONTO_LAT_MAX = 43.6, 43.7
TORONTO_LON_MIN, TORONTO_LON_MAX = -79.6, -79.3

for name, vertex in graph._vertices.items():
    # here we assume lat/lng can be derived elsewhere or stored alongside
    # since _Vertex does not contain lat/lng, this should be from original JSON
    # you might modify load_graph_from_json to return this too if needed
    pass  # fill this in with actual coordinate extraction

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
        <button onclick=\"clickedMarkers.push('{label}'); document.getElementById('selection').innerHTML += '{label} → '; console.log(clickedMarkers);\">Select</button>
        """
        popup = folium.Popup(popup_html, max_width=300)
        folium.Marker(location=coords, popup=popup, tooltip=label).add_to(m)

    # Draw the line if path exists
    if last_path:
        route_coords = [markers[n] for n in last_path if n in markers]
        if len(route_coords) >= 2:
            folium.PolyLine(route_coords, color="blue", weight=5, tooltip="Route").add_to(m)

    return m._repr_html_()

@app.route('/calculate', methods=['POST'])
def calculate():
    global last_path, last_result
    data = request.get_json()
    nodes = data.get("nodes", [])

    if len(nodes) < 2:
        return jsonify({"error": "Please select at least two locations."})

    start = nodes[0]
    rest = nodes[1:]
    path = greedy_dijkstra_method1(graph, start, rest)

    try:
        distance = graph.comp_path(path)
    except:
        return jsonify({"error": "Could not compute full path."})

    last_path = path
    last_result = {
        "path": path,
        "distance": distance,
        "message": "Success"
    }
    return jsonify(last_result)

if __name__ == '__main__':
    app.run(debug=True)