# main.py
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_geology_from_egdi(lat: float, lng: float):
    try:
        bbox = f"{lng-0.001},{lat-0.001},{lng+0.001},{lat+0.001}"
        url = (
            "https://egdi.geology.cz/arcgis/services/OneGeologyEurope/OneGeologyEurope_1M/MapServer/WMSServer?"
            "SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&FORMAT=application/json&TRANSPARENT=true"
            "&QUERY_LAYERS=1&LAYERS=1&INFO_FORMAT=application/json&X=1&Y=1&SRS=EPSG:4326"
            f"&WIDTH=1&HEIGHT=1&BBOX={bbox}"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("features") and len(data["features"]) > 0:
            description = data["features"][0].get("properties", {}).get("lithology", "No description available")
            return description
        else:
            return "Geological data not found at this location."
    except Exception:
        return "Could not connect to the geological data service (EGDI)."

@app.get("/get_geodata")
def get_geodata_for_coords(lat: float, lng: float):
    geological_formation = get_geology_from_egdi(lat, lng)
    success = "Could not connect" not in geological_formation

    return {
        "success": success,
        "received_coords": {"latitude": lat, "longitude": lng},
        "geotechnical": {"geologicalFormation": geological_formation}
    }
