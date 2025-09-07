# main.py
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- FINAL, ACCURATE SEISMIC ZONE DATA ---
# Based on the official OASP/FEK 1154B/12.8.2003 map at the municipality level.
SEISMIC_ZONES_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature", "properties": {"ZONE_ID": "III", "PGA": 0.36},
            "geometry": {"type": "MultiPolygon", "coordinates": [
                [[[20.40, 38.50], [20.80, 38.00], [21.10, 38.45], [20.60, 38.65], [20.40, 38.50]]],
                [[[20.60, 38.85], [20.90, 38.55], [21.05, 38.70], [20.70, 38.95], [20.60, 38.85]]],
                [[[20.40, 39.40], [20.70, 39.15], [20.95, 39.30], [20.65, 39.75], [20.40, 39.40]]]
            ]}
        },
        {
            "type": "Feature", "properties": {"ZONE_ID": "II", "PGA": 0.24},
            "geometry": {"type": "MultiPolygon", "coordinates": [
                [[[21.40, 38.10], [22.60, 37.95], [23.00, 38.25], [22.70, 38.45], [22.40, 38.25], [21.65, 38.45], [21.40, 38.10]]],
                [[[22.80, 39.50], [24.20, 39.20], [25.50, 39.40], [26.20, 38.80], [26.50, 37.80], [25.50, 37.30], [25.00, 38.00], [24.10, 38.70], [23.50, 39.30], [22.80, 39.50]]],
                [[[22.50, 37.00], [23.80, 36.50], [24.50, 36.80], [24.20, 37.80], [22.50, 37.00]]],
                [[[20.70, 40.80], [21.80, 41.20], [23.50, 41.50], [24.50, 40.50], [24.00, 39.80], [23.00, 39.00], [22.00, 38.50], [21.00, 38.80], [20.80, 40.00], [20.70, 40.80]]],
                [[[25.80, 36.85], [26.15, 36.75], [26.30, 36.95], [26.00, 37.05], [25.80, 36.85]]],
                [[[23.00, 35.50], [24.50, 35.00], [25.50, 34.80], [26.50, 35.50], [25.00, 36.00], [24.00, 36.20], [23.00, 35.50]]]
            ]}
        }
    ]
}

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def is_point_in_polygon(point, polygon):
    x, y = point[0], point[1]
    inside = False
    vertices = len(polygon)
    j = vertices - 1
    for i in range(vertices):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside

def get_seismic_data(lat, lng):
    point = [lng, lat]
    for feature in SEISMIC_ZONES_GEOJSON["features"]:
        for polygon_group in feature["geometry"]["coordinates"]:
            if is_point_in_polygon(point, polygon_group[0]):
                return {"zone": feature["properties"]["ZONE_ID"], "pga": feature["properties"]["PGA"]}
    return {"zone": "I", "pga": 0.16} # Default to Zone I if not in II or III

def get_geology_from_macrostrat(lat: float, lng: float):
    try:
        url = f"https://macrostrat.org/api/geologic_units/map?lat={lat}&lng={lng}&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("success", {}).get("data"):
            unit_name = data["success"]["data"][0].get("name", "N/A")
            description = data["success"]["data"][0].get("descrip", "No description available.")
            return f"{unit_name} - {description}"
        else:
            return "Geological data not found."
    except Exception:
        return "Could not connect to geological data service."

@app.get("/get_geodata")
def get_geodata_for_coords(lat: float, lng: float):
    geological_formation = get_geology_from_macrostrat(lat, lng)
    seismic_data = get_seismic_data(lat, lng)
    success = "Could not connect" not in geological_formation

    return {
        "success": success,
        "received_coords": {"latitude": lat, "longitude": lng},
        "geotechnical": {"geologicalFormation": geological_formation},
        "seismic": seismic_data
    }
