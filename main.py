"""
This module implements a Flask web application that renders an interactive map using Folium.
Users can select markers to calculate a path based on a custom greedy Dijkstra algorithm.
The application relies on a pre-built graph (loaded from JSON) and displays the computed route on the map.

Preconditions:
    - The file "graph_output.json" must exist and be correctly formatted.
    - The modules 'json_to_class' and 'pj2_graph_alg' must be available and functional.
    - The 'markers' dictionary must contain valid coordinate pairs.

Invariants:
    - Global variables 'last_path' and 'last_result' store the most recent computed path and result,
      and are updated only within the defined endpoints.
    - The map is re-rendered with each request to reflect the latest global state.
"""

from flask import Flask, render_template, request, jsonify
import folium
from json_to_class import load_graph_from_json
from pj2_graph_alg import greedy_dijkstra_method1
import os

app = Flask(__name__)

# ===== Load Graph and Coordinates =====
# Preconditions: "graph_output.json" should exist and contain valid graph and marker data.
graph, markers = load_graph_from_json("graph_output.json")

# ===== Global State =====
# Invariants: last_path and last_result always reflect the last computed route and result.
last_path = []
last_result = {}


@app.route('/')
def index():
    """
    Render the interactive map page.

    This function creates a Folium map centered at a default location and adds markers with clickable
    buttons that allow users to select nodes. It also draws the last computed route if available.

    Preconditions:
        - 'markers' is a dict with marker labels as keys and coordinate pairs (list or tuple) as values.
        - Global variables 'last_path' and 'last_result' are properly maintained.

    Invariants:
        - The rendered map always includes all markers from 'markers'.
        - If a valid route exists in 'last_path', it is drawn on the map.

    Returns:
        Rendered HTML page from the 'map.html' template.
    """
    # Create a map centered at a default location
    m = folium.Map(location=[43.6631778, -79.3946746], zoom_start=17)

    # Add markers to the map with popups including a "Select" button
    for label, coords in markers.items():
        popup_html = f"""
        <b>{label}</b><br>
        <button onclick="clickedMarkers.push('{label}'); document.getElementById('selection').innerHTML += '{label} → '; console.log(clickedMarkers);">Select</button>
        """
        popup = folium.Popup(popup_html, max_width=300)
        folium.Marker(location=coords, popup=popup, tooltip=label).add_to(m)

    # If a route has been computed, draw the polyline on the map
    if last_path:
        # Preconditions: all nodes in 'last_path' must exist in markers
        route_coords = [markers[n] for n in last_path if n in markers]
        if len(route_coords) >= 2:
            folium.PolyLine(route_coords, color="blue", weight=5, tooltip="Route").add_to(m)

    # Prepare the HTML for displaying the result on the map
    result_html = ""
    if last_result:
        result_html = (
            f"<b>Path:</b> {' → '.join(last_result['path'])}<br>"
            f"<b>Duration:</b> {last_result['distance']} min<br>"
            f"{last_result['message']}"
        )

    # JavaScript and HTML code for the selection panel
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
            fetch('/calculate', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ nodes: clickedMarkers }})
            }})
            .then(response => response.json())
            .then(data => {{
                window.location.reload();
            }});
        }}

        function clearSelection() {{
            clickedMarkers = [];
            document.getElementById("selection").innerHTML = "<b>Selected:</b> ";
            document.getElementById("result").innerHTML = "";
        }}
    </script>
    """

    # Inject the JavaScript and HTML into the map and save it to the template
    m.get_root().html.add_child(folium.Element(js_code))
    m.save("templates/map.html")

    return render_template("map.html")


@app.route('/calculate', methods=['POST'])
def calculate():
    """
    Calculate the optimal path based on user-selected nodes using a greedy Dijkstra algorithm.

    The function expects a JSON POST request containing a list of node labels under the key 'nodes'.
    It computes the route starting from the first node using 'greedy_dijkstra_method1' and calculates
    the total distance (converted to minutes) using a simplified complete graph method.

    Preconditions:
        - The POST request JSON must contain a key "nodes" with a list of node labels.
        - There must be at least 2 nodes selected; otherwise, a warning message is returned.
        - The global 'graph' object must support 'generate_complete_graph' and the resulting simplified
          graph must support 'comp_path' method.

    Invariants:
        - The global variables 'last_path' and 'last_result' are updated only in this function.

    Returns:
        JSON response with the computed path, distance (in minutes), and a status message.
    """
    global last_path, last_result
    data = request.get_json()
    nodes = data.get("nodes", [])

    if len(nodes) < 2:
        last_result = {
            "path": nodes,
            "distance": 0,
            "message": "❗ Select at least 2 nodes."
        }
        return jsonify(last_result)

    # Compute path starting from the first node using the greedy Dijkstra method
    start = nodes[0]
    path = greedy_dijkstra_method1(graph, start, nodes)

    # Generate a simplified complete graph for the selected nodes
    simp_graph = graph.generate_complete_graph(nodes)
    # Calculate total distance; assume the distance is given in seconds and convert to minutes
    distance = simp_graph.comp_path(nodes) / 60

    # Update global state with the new path and result
    last_path = path
    last_result = {
        "path": path,
        "distance": round(distance, 2),
        "message": "✅ Path calculated successfully."
    }
    return jsonify(last_result)


if __name__ == '__main__':
    """
    Entry point for the Flask application.

    This block ensures that the 'templates' directory exists before starting the Flask development server.

    Preconditions:
        - The operating system must permit creating directories if they do not exist.

    Invariants:
        - The application runs in debug mode.
    """
    if not os.path.exists("templates"):
        os.mkdir("templates")
    app.run(debug=True)
    # import python_ta
    #
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['E1136', 'W0221'],
    #     'max-nested-blocks': 4
    # })
