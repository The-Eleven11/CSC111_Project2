from flask import Flask, render_template, request, jsonify
import folium
import networkx as nx
from math import radians, cos, sin, asin, sqrt
from itertools import permutations

app = Flask(__name__)

markers = {
    "City Hall": (43.65107, -79.347015),
    "CN Tower": (43.642566, -79.387057),
    "Downtown Core": (43.6532, -79.3832),
    "Pearson Airport": (43.6777, -79.6248)
}


# Haversine distance
def haversine(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))


# Build Graph
G = nx.Graph()
for label1, coord1 in markers.items():
    G.add_node(label1, pos=coord1)
    for label2, coord2 in markers.items():
        if label1 != label2 and not G.has_edge(label1, label2):
            dist = haversine(coord1, coord2)
            G.add_edge(label1, label2, weight=dist)


@app.route('/')
def index():
    m = folium.Map(location=[43.65107, -79.347015], zoom_start=12)

    # Add markers with buttons that work inside the iframe (self-contained)
    for label, (lat, lon) in markers.items():
        popup_html = f"""
            <b>Marker {label}</b><br>
            <button onclick="clickedMarkers.push('{label}'); document.getElementById('selection').innerHTML += '{label} '; console.log('Clicked:', clickedMarkers);">Add This Marker</button>
        """
        popup = folium.Popup(popup_html, max_width=250)
        folium.Marker([lat, lon], popup=popup, tooltip=f"Marker {label}").add_to(m)

    # Inject UI and JS inside the map page
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
                    document.getElementById("result").innerHTML =
                        "📍 <b>Path:</b> " + path + "<br>🧭 <b>Distance:</b> " + dist + " km";
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

    m.save("static/map.html")
    return render_template("map.html")


@app.route('/shortest_path', methods=['POST'])
def shortest_path():
    data = request.get_json()
    nodes = data.get("nodes", [])

    if len(nodes) < 2:
        return jsonify({"path": nodes, "message": "Select at least 2 nodes"})

    min_path = None
    min_distance = float('inf')

    for perm in permutations(nodes):
        total = 0
        for i in range(len(perm) - 1):
            total += G[perm[i]][perm[i + 1]]['weight']
        if total < min_distance:
            min_distance = total
            min_path = perm

    return jsonify({
        "path": list(min_path),
        "distance": round(min_distance, 2)
    })


if __name__ == "__main__":
    app.run(debug=True)


@app.route('/shortest_path', methods=['POST'])
def shortest_path():
    data = request.get_json()
    nodes = data.get("nodes", [])

    if len(nodes) < 2:
        return jsonify({"path": nodes, "message": "Need at least 2 nodes"})

    # Solve approximate TSP (visiting all clicked nodes)
    min_path = None
    min_distance = float('inf')

    for perm in permutations(nodes):
        total = 0
        for i in range(len(perm) - 1):
            total += G[perm[i]][perm[i + 1]]['weight']
        if total < min_distance:
            min_distance = total
            min_path = perm

    return jsonify({
        "path": list(min_path),
        "distance": round(min_distance, 2)
    })
