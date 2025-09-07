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

def get_geology_from_macrostrat(lat: float, lng: float):
    """
    Fetches geological data from the Macrostrat open database.
    This is a more reliable alternative to the EGDI WMS service.
    """
    try:
        url = f"https://macrostrat.org/api/geologic_units/map?lat={lat}&lng={lng}&format=json"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success", {}).get("data"):
            # Extract the name of the geological unit
            unit_name = data["success"]["data"][0].get("name", "N/A")
            # Extract the general description
            description = data["success"]["data"][0].get("descrip", "No description available.")
            
            # Combine them for a useful result
            return f"{unit_name} - {description}"
        else:
            return "Geological data not found at this location."

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Macrostrat: {e}")
        return "Could not connect to the geological data service (Macrostrat)."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "An error occurred while processing geological data."


@app.get("/get_geodata")
def get_geodata_for_coords(lat: float, lng: float):
    """
    Main endpoint that gathers data from various sources.
    """
    # Use the new, more reliable data source
    geological_formation = get_geology_from_macrostrat(lat, lng)
    
    success = "Could not connect" not in geological_formation

    return {
        "success": success,
        "received_coords": {"latitude": lat, "longitude": lng},
        "geotechnical": {"geologicalFormation": geological_formation}
    }
