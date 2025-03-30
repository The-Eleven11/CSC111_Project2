from flask import Flask, render_template, request, jsonify
import folium
from json_to_class import load_graph_from_json
from pj2_graph_alg import greedy_dijkstra_method1
import os

app = Flask(__name__)

# ===== Load Graph and Coordinates =====
graph, markers = load_graph_from_json("graph_output.json")

# ===== Global State =====
last_path = []
last_result = {}

# ===== Flask Routes =====
@app.route('/')
def index():
    m = folium.Map(location=[43.6631778, -79.3946746], zoom_start=17)

    # 在地图上添加标记以及弹出按钮
    for label, coords in markers.items():
        popup_html = f"""
        <b>{label}</b><br>
        <button onclick="clickedMarkers.push('{label}'); document.getElementById('selection').innerHTML += '{label} → '; console.log(clickedMarkers);">Select</button>
        """
        popup = folium.Popup(popup_html, max_width=300)
        folium.Marker(location=coords, popup=popup, tooltip=label).add_to(m)

    # 绘制已选择的路径
    if last_path:
        route_coords = [markers[n] for n in last_path if n in markers]
        if len(route_coords) >= 2:
            folium.PolyLine(route_coords, color="blue", weight=5, tooltip="Route").add_to(m)

    # 注入前端 UI 与 JS 代码
    result_html = ""
    if last_result:
        result_html = f"<b>Path:</b> {' → '.join(last_result['path'])}<br>" \
                      f"<b>Duration:</b> {last_result['distance']} seconds<br>" \
                      f"{last_result['message']}"

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

    m.get_root().html.add_child(folium.Element(js_code))
    m.save("templates/map.html")

    return render_template("map.html")

@app.route('/calculate', methods=['POST'])
def calculate():
    global last_path, last_result
    data = request.get_json()
    nodes = data.get("nodes", [])

    if len(nodes) < 2:
        last_result = {"path": nodes, "distance": 0, "message": "❗ Select at least 2 nodes."}
        return jsonify(last_result)

    start = nodes[0]
    path = greedy_dijkstra_method1(graph, start, nodes)

    simp_graph = graph.generate_complete_graph(nodes)
    # distance = graph.comp_path(path)
    distance = simp_graph.comp_path(nodes)
    # try:
    #     distance = graph.comp_path(path)
    # except Exception as e:
    #     return jsonify({"error": f"Could not compute path: {str(e)}"})

    last_path = path
    last_result = {
        "path": path,
        "distance": round(distance, 2),
        "message": "✅ Path calculated successfully."
    }
    return jsonify(last_result)

if __name__ == '__main__':
    if not os.path.exists("templates"):
        os.mkdir("templates")
    app.run(debug=True)