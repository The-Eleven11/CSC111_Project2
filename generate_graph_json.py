import csv
import json
import time
import os
import math
import googlemaps


API_KEY = "YOUR KEY"
gmaps = googlemaps.Client(key=API_KEY)


def get_geocode(address):
    """
    Get latitude and longitude for a given address using the Geocoding API.
    """
    results = gmaps.geocode(address)
    if results:
        location = results[0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        print(f"Geocode not found for {address}")
        return None, None


def batch_distance_matrix(origins, destinations, mode="walking", max_elements=100):
    """
    Query the Distance Matrix API in batches so that each request contains at most
    max_elements (i.e. len(batch_origins) * len(batch_destinations) <= max_elements).

    Returns a dictionary where the keys are the origin strings (e.g. "lat,lng")
    and the values are lists of tuples (destination, distance, duration).

    IMPORTANT NOTICE: THIS PART DID WITH HELP WITH CHATGPT
    """
    candidate_edges = {origin: [] for origin in origins}
    batch_size = int(math.floor(math.sqrt(max_elements)))
    for i in range(0, len(origins), batch_size):
        origin_batch = origins[i:i + batch_size]
        for j in range(0, len(destinations), batch_size):
            destination_batch = destinations[j:j + batch_size]
            try:
                matrix_result = gmaps.distance_matrix(
                    origins=origin_batch,
                    destinations=destination_batch,
                    mode=mode
                )
            except Exception as e:
                print(f"Error with batch request: {e}")
                continue

            for i_idx, origin in enumerate(origin_batch):
                row = matrix_result.get("rows", [])[i_idx]
                elements = row.get("elements", [])
                for j_idx, element in enumerate(elements):
                    dest = destination_batch[j_idx]
                    if origin == dest:
                        continue
                    if element.get("status") != "OK":
                        continue
                    distance = element["distance"]["value"]  # in meters
                    duration = element["duration"]["value"]  # in seconds
                    candidate_edges[origin].append((dest, distance, duration))
            time.sleep(0.1)
    return candidate_edges



buildings = []
with open("buildings.csv", newline="") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if row:
            buildings.append(row[0].strip())



special_building = "Keep@Downsview, Toronto, ON, Canada"
special_neighbors = [
    "1 Spadina Crescent, Toronto, ON, Canada",
    "Robarts Library, Toronto, ON, Canada",
    "Gerstein Science Information Center, Toronto, ON, Canada",
    "John M. Kelly Library, Toronto, ON, Canada",
    "Ontario Institute for Studies in Education, Toronto, ON, Canada"
]


nodes = {}
ordered_buildings = []
ordered_coords = []

for b in buildings:
    lat, lng = get_geocode(b)
    if lat is None or lng is None:
        continue
    nodes[b] = {"name": b, "lat": lat, "lng": lng, "edges": []}
    ordered_buildings.append(b)
    ordered_coords.append(f"{lat},{lng}")


coord_to_building = {coord: b for b, coord in zip(ordered_buildings, ordered_coords)}


candidate_edges_by_coord = batch_distance_matrix(
    origins=ordered_coords,
    destinations=ordered_coords,
    mode="walking",
    max_elements=100
)

####################################################################################################################
# Convert the candidate edges so that keys are building names rather than coordinate strings.
# THIS PART DID WITH CHATGPT
candidate_edges = {b: [] for b in ordered_buildings}
for origin_coord, edges in candidate_edges_by_coord.items():
    origin_building = coord_to_building.get(origin_coord)
    if not origin_building:
        continue
    for dest_coord, distance, duration in edges:
        dest_building = coord_to_building.get(dest_coord)
        if dest_building:
            candidate_edges[origin_building].append((dest_building, distance, duration))

for building, candidates in candidate_edges.items():
    if building == special_building:
        continue
    within_150 = [c for c in candidates if c[1] <= 150]
    if len(within_150) >= 5:
        selected = within_150
    else:
        selected = within_150.copy()
        candidates_sorted = sorted(candidates, key=lambda x: x[1])
        for cand in candidates_sorted:
            if cand not in selected:
                selected.append(cand)
            if len(selected) >= 5:
                break
    for dest, dist, dur in selected:
        edge = {"neighbor": dest, "distance": dist, "duration": dur, "mode": "walking"}
        nodes[building]["edges"].append(edge)

if special_building in nodes:
    nodes[special_building]["edges"] = []
    origin_coord = f"{nodes[special_building]['lat']},{nodes[special_building]['lng']}"
    special_destinations = []
    special_dest_buildings = []
    for nb in special_neighbors:
        if nb in nodes:
            coord = f"{nodes[nb]['lat']},{nodes[nb]['lng']}"
        else:
            lat, lng = get_geocode(nb)
            time.sleep(0.1)
            if lat is None or lng is None:
                continue
            coord = f"{lat},{lng}"
        special_destinations.append(coord)
        special_dest_buildings.append(nb)
    try:
        special_result = gmaps.distance_matrix(
            origins=[origin_coord],
            destinations=special_destinations,
            mode="driving"
        )
    except Exception as e:
        print(f"Error with special building request: {e}")
        special_result = None
    if special_result:
        elements = special_result["rows"][0]["elements"]
        for idx, element in enumerate(elements):
            nb = special_dest_buildings[idx]
            if element.get("status") != "OK":
                continue
            distance = element["distance"]["value"]
            duration = element["duration"]["value"]
            edge = {"neighbor": nb, "distance": distance, "duration": duration, "mode": "driving"}
            nodes[special_building]["edges"].append(edge)
#################################################################################################


#OUTPUT JSON File
graph = {"nodes": list(nodes.values())}
file_name = "graph_output.json"
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, file_name)

with open(file_path, "w", encoding="utf-8") as json_file:
    json.dump(graph, json_file, indent=4, ensure_ascii=False)
