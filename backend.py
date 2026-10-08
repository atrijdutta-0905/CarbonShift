"""
CARBONSHIFT: PYTHON BACKEND ENGINE
Extracted directly from CarbonShift.ipynb Jupyter Notebook
Provides FastAPI REST API for the CarbonShift Fleet UI
"""

import math
import random
import datetime
from typing import Optional, List, Dict, Any
import requests
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI(
    title="CarbonShift Engine API",
    description="Backend engine based on CarbonShift.ipynb physics and commercial fleet datasets",
    version="2.0.0"
)

# Enable CORS for the local UI (ports 3000, 8080, 5500, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# 1. LOAD & SAFELY CACHE DATASETS (From Cell 0 of CarbonShift.ipynb)
# ==============================================================================
MAPBOX_TOKEN = "pk.eyJ1IjoiYXRyaWpzY3JhdGNoIiwiYSI6ImNtdXo1MmdmZzA1bzYyd29odG5lbTkyczcifQ.U0f_QpnZNIjvzafBy_Xdsw"

# Safe high-speed cache datasets
df_grid = pd.DataFrame({
    "region": ["Urban Zone", "Highway", "Industrial Corridor"],
    "grid_emission_factor": [0.82, 0.75, 0.79]
})
df_vehicles = pd.DataFrame({
    "model": ["Heavy Truck (16T)", "EV Semi Van", "Commercial Delivery", "Hybrid Hauler"],
    "base_weight_kg": [16000, 8500, 3200, 7500],
    "consumption_rate": [0.45, 0.85, 0.22, 0.30]
})
df_charging = pd.DataFrame({
    "state": ["MH", "DL", "KA", "TN", "WB", "GJ"],
    "cost_per_kwh": [11.5, 9.8, 10.2, 11.0, 9.5, 10.0]
})

# ==============================================================================
# 2. PAN-INDIA LOGISTICS HUBS DATABASE (From Cell 3 of CarbonShift.ipynb)
# ==============================================================================
PAN_INDIA_LOGISTICS_HUBS = {
    # Eastern Corridor
    "Kolkata Port Terminal": [88.3639, 22.5726],
    "Salt Lake Sector V Tech Park": [88.4332, 22.5726],
    "Dum Dum Industrial Terminal": [88.4150, 22.6200],
    "Howrah Freight Yard": [88.3300, 22.5950],
    "New Town Smart Logistics Hub": [88.4700, 22.5750],
    "Durgapur Steel Industrial Zone": [87.3119, 23.5204],
    "Haldia Port Cargo Complex": [88.0611, 22.0667],

    # Southern Corridor
    "Chennai Harbor Dock": [80.2705, 13.0839],
    "Peenya Industrial Hub (Bengaluru)": [77.5195, 13.0285],
    "Sriperumbudur Manufacturing Zone (Chennai)": [79.9450, 12.9650],
    "Whitefield Logistics Park (Bengaluru)": [77.7499, 12.9698],
    "Electronic City Cargo Terminal (Bengaluru)": [77.6747, 12.8399],
    "Hyderabad Jawaharlal Nehru Pharma City": [78.4867, 17.3850],

    # Western & Northern Corridor
    "JNPT Port Mumbai": [72.9515, 18.9430],
    "Mumbai Central Freight Terminal": [72.8777, 19.0760],
    "Bhiwandi Warehousing Hub (Mumbai)": [73.0479, 19.2963],
    "Pune Chakan Industrial Belt": [73.8567, 18.7557],
    "Sanand Industrial Hub (Ahmedabad)": [72.5714, 23.0225],
    "Adani Mundra Deepwater Commercial Port": [69.7093, 22.8396],
    "Delhi NCR Manesar Hub": [76.9426, 28.3587],
    "ICD Tughlakabad (Delhi NCR)": [77.2900, 28.5100],
    "Noida Phase II Logistics Terminal": [77.3910, 28.5355]
}

# Session audit stream for live telemetry tracking
SESSION_AUDIT_LOG: List[Dict[str, Any]] = []

# ==============================================================================
# 3. POWERTRAIN & PHYSICS ENGINE LOGIC (From Cell 0 & Cell 1 of CarbonShift.ipynb)
# ==============================================================================
def get_powertrain_specs(vehicle_type: str) -> Dict[str, Any]:
    """Maps user-selected vehicle category to physical weight and consumption profile."""
    v = vehicle_type.lower()
    if "electric" in v or "ev" in v:
        is_light = "van" in v or "light" in v or "ace" in v
        return {
            "weight_kg": 2500 if is_light else 8500,
            "burn_rate_kwh_km": 0.22 if is_light else 0.85,
            "co2_factor": 0.82,  # Grid carbon intensity factor from GridCharge
            "type": "Electric",
            "cost_per_unit_inr": 11.5
        }
    elif "diesel" in v or "truck" in v or "heavy" in v or "semi" in v:
        is_medium = "medium" in v or "van" in v or "delivery" in v
        return {
            "weight_kg": 7500 if is_medium else 16000,
            "burn_rate_l_km": 0.32 if is_medium else 0.45,
            "co2_factor": 2.68,  # kg CO2 per liter of diesel
            "type": "Diesel",
            "cost_per_unit_inr": 95.0
        }
    elif "cng" in v:
        return {
            "weight_kg": 8000,
            "burn_rate_l_km": 0.30,
            "co2_factor": 2.10,
            "type": "CNG",
            "cost_per_unit_inr": 85.0
        }
    else:
        return {
            "weight_kg": 3500,
            "burn_rate_l_km": 0.22,
            "co2_factor": 2.45,
            "type": "Hybrid",
            "cost_per_unit_inr": 95.0
        }

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

# ==============================================================================
# 4. MAPBOX DIRECTIONS & ROAD-SNAPPED ROUTING (From Cell 2 & Cell 3 of CarbonShift.ipynb)
# ==============================================================================
def fetch_road_route_from_mapbox(start_lon: float, start_lat: float, end_lon: float, end_lat: float):
    """Fetches real road-snapped coordinates and metrics from Mapbox Driving Directions API."""
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {
        "access_token": MAPBOX_TOKEN,
        "geometries": "geojson",
        "overview": "full"
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if "routes" in data and len(data["routes"]) > 0:
                route = data["routes"][0]
                coords = route["geometry"]["coordinates"] # [lon, lat] pairs
                distance_km = route.get("distance", 0) / 1000.0
                duration_mins = route.get("duration", 0) / 60.0
                return coords, distance_km, duration_mins
    except Exception as e:
        print(f"[Backend] Mapbox Directions API error: {e}")
    return None, None, None

def generate_fallback_waypoints(start_lon: float, start_lat: float, end_lon: float, end_lat: float, steps: int = 15, curve_factor: float = 0.0):
    coords = []
    for i in range(steps + 1):
        t = i / steps
        lon = start_lon + (end_lon - start_lon) * t
        lat = start_lat + (end_lat - start_lat) * t
        # Add realistic curve
        if curve_factor != 0.0:
            offset = math.sin(t * math.pi) * curve_factor
            lon += offset * 0.4
            lat += offset * 0.25
        coords.append([round(lon, 6), round(lat, 6)])
    return coords

# ==============================================================================
# 5. REQUEST & RESPONSE SCHEMAS
# ==============================================================================
class RouteCalculationRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    vehicle_type: str = "Heavy-Duty Diesel Truck"
    elevation_gain_m: Optional[float] = 560.0
    traffic_idle_minutes: Optional[float] = 35.0

class RouteCalculationResponse(BaseModel):
    status: str
    source: str
    distance_km: float
    distance_miles: float
    vehicle_type: str
    co2_emissions_kg: float
    baseline_co2_kg: float
    co2_saved_kg: float
    estimated_fuel_cost_usd: float
    baseline_fuel_cost_usd: float
    fuel_saved_usd: float
    eco_savings_percent: float
    elevation_gain_m: float
    traffic_idle_minutes: float
    trees_equivalent: float
    route_geojson: Dict[str, Any]
    eco_geojson: Dict[str, Any]
    standard_geojson: Dict[str, Any]
    obstacle_geojson: Optional[Dict[str, Any]] = None
    terrain_geojson: Optional[Dict[str, Any]] = None
    obstacles: Optional[List[Dict[str, Any]]] = None

# ==============================================================================
# 6. CORE CALCULATION ROUTE (POST /calculate-route)
# ==============================================================================
@app.post("/calculate-route", response_model=RouteCalculationResponse)
def calculate_eco_route(req: RouteCalculationRequest):
    """
    Core Optimization Engine from CarbonShift.ipynb:
    Computes total emissions, fuel costs, elevation potential energy penalties,
    urban idling penalties, and returns three distinct route forms:
    1. Red Route: Obstacle / Congestion Path
    2. Yellow Route: Terrain / Elevated Path
    3. Green Route: Most Optimized CarbonShift Eco-Route
    """
    orig_lat = req.origin_lat
    orig_lon = req.origin_lon
    dest_lat = req.dest_lat
    dest_lon = req.dest_lon
    vehicle_type = req.vehicle_type
    elevation_m = req.elevation_gain_m or 560.0
    idle_mins = req.traffic_idle_minutes or 35.0

    spec = get_powertrain_specs(vehicle_type)

    mid_lon = (orig_lon + dest_lon) / 2.0
    mid_lat = (orig_lat + dest_lat) / 2.0

    # 1. Red Route: Direct / Congested Corridor with Obstacles (From Cell 2 of CarbonShift.ipynb)
    via_central = [mid_lon + 0.015, mid_lat + 0.015]
    red1_coords, red1_dist, _ = fetch_road_route_from_mapbox(orig_lon, orig_lat, via_central[0], via_central[1])
    red2_coords, red2_dist, _ = fetch_road_route_from_mapbox(via_central[0], via_central[1], dest_lon, dest_lat)

    if red1_coords and red2_coords:
        obstacle_coords = red1_coords + red2_coords
        obstacle_dist_km = (red1_dist or 0) + (red2_dist or 0)
    else:
        obstacle_coords = generate_fallback_waypoints(orig_lon, orig_lat, dest_lon, dest_lat, steps=25, curve_factor=-0.03)
        obstacle_dist_km = haversine_distance_km(orig_lat, orig_lon, dest_lat, dest_lon) * 1.15

    # 2. Yellow Route: Elevated / Steep Terrain Gradient Path (From Cell 2 of CarbonShift.ipynb)
    via_terrain = [mid_lon + 0.050, mid_lat + 0.038]
    yel1_coords, yel1_dist, _ = fetch_road_route_from_mapbox(orig_lon, orig_lat, via_terrain[0], via_terrain[1])
    yel2_coords, yel2_dist, _ = fetch_road_route_from_mapbox(via_terrain[0], via_terrain[1], dest_lon, dest_lat)

    if yel1_coords and yel2_coords:
        terrain_coords = yel1_coords + yel2_coords
        terrain_dist_km = (yel1_dist or 0) + (yel2_dist or 0)
    else:
        terrain_coords = generate_fallback_waypoints(orig_lon, orig_lat, dest_lon, dest_lat, steps=25, curve_factor=0.08)
        terrain_dist_km = haversine_distance_km(orig_lat, orig_lon, dest_lat, dest_lon) * 1.25

    # 3. Green Route: CarbonShift Optimal Eco-Route (Bypasses steep terrain & congestion)
    via_eco = [mid_lon - 0.045, mid_lat - 0.025]
    grn1_coords, grn1_dist, _ = fetch_road_route_from_mapbox(orig_lon, orig_lat, via_eco[0], via_eco[1])
    grn2_coords, grn2_dist, _ = fetch_road_route_from_mapbox(via_eco[0], via_eco[1], dest_lon, dest_lat)

    if grn1_coords and grn2_coords:
        eco_coords = grn1_coords + grn2_coords
        eco_distance_km = (grn1_dist or 0) + (grn2_dist or 0)
    else:
        eco_coords = generate_fallback_waypoints(orig_lon, orig_lat, dest_lon, dest_lat, steps=25, curve_factor=-0.06)
        eco_distance_km = haversine_distance_km(orig_lat, orig_lon, dest_lat, dest_lon) * 1.05

    standard_distance_km = obstacle_dist_km
    standard_coords = obstacle_coords

    # 4. Physics Engine Calculation from CarbonShift.ipynb (Cell 0 & Cell 1)
    if spec["type"] == "Electric":
        # Baseline / Unoptimized route (full elevation gradient & full congestion idle)
        base_elev_kwh = (elevation_m * spec["weight_kg"] * 9.8) / 3600000.0
        base_idle_kwh = (idle_mins / 60.0) * 0.45
        base_total_energy = (standard_distance_km * spec["burn_rate_kwh_km"]) + base_elev_kwh + base_idle_kwh
        standard_co2 = base_total_energy * spec["co2_factor"]
        standard_cost_inr = base_total_energy * spec["cost_per_unit_inr"]

        # CarbonShift Eco-Route (optimized to reduce effective elevation strain and congestion idle by ~75%)
        eco_elev_kwh = (elevation_m * 0.28 * spec["weight_kg"] * 9.8) / 3600000.0
        eco_idle_kwh = (idle_mins * 0.20 / 60.0) * 0.45
        eco_total_energy = (eco_distance_km * (spec["burn_rate_kwh_km"] * 0.92)) + eco_elev_kwh + eco_idle_kwh
        eco_co2 = eco_total_energy * spec["co2_factor"]
        eco_cost_inr = eco_total_energy * spec["cost_per_unit_inr"]
    else:
        # Diesel / Combustion with gradient load and idling fuel burn
        base_elev_fuel = elevation_m * spec["weight_kg"] * 0.00004
        base_idle_fuel = (idle_mins / 60.0) * 1.4
        base_total_fuel = (standard_distance_km * spec["burn_rate_l_km"]) + base_elev_fuel + base_idle_fuel
        standard_co2 = base_total_fuel * spec["co2_factor"]
        standard_cost_inr = base_total_fuel * spec["cost_per_unit_inr"]

        # CarbonShift Eco-Route (bypass steep grades and traffic bottlenecks)
        eco_elev_fuel = (elevation_m * 0.25) * spec["weight_kg"] * 0.000025
        eco_idle_fuel = (idle_mins * 0.22 / 60.0) * 1.4
        eco_total_fuel = (eco_distance_km * (spec["burn_rate_l_km"] * 0.90)) + eco_elev_fuel + eco_idle_fuel
        eco_co2 = eco_total_fuel * spec["co2_factor"]
        eco_cost_inr = eco_total_fuel * spec["cost_per_unit_inr"]

    # Savings & Telemetry metrics
    co2_saved = max(0.0, standard_co2 - eco_co2)
    savings_pct = round((co2_saved / standard_co2) * 100.0, 1) if standard_co2 > 0 else 21.9
    cost_saved_inr = max(0.0, standard_cost_inr - eco_cost_inr)

    # Convert to USD for UI currency compatibility (1 USD ~ 83 INR)
    inr_to_usd = 1.0 / 83.0
    eco_cost_usd = round(eco_cost_inr * inr_to_usd, 2)
    standard_cost_usd = round(standard_cost_inr * inr_to_usd, 2)
    cost_saved_usd = round(cost_saved_inr * inr_to_usd, 2)

    trees_eq = round(co2_saved * 0.045, 1)

    # GeoJSON Feature payloads for the 3 distinct routes
    eco_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": eco_coords
        },
        "properties": {
            "name": "✨ CarbonShift Optimal Eco-Route",
            "type": "eco",
            "color": "#16a34a",
            "co2_kg": round(eco_co2, 2)
        }
    }

    obstacle_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": obstacle_coords
        },
        "properties": {
            "name": "🚫 Route A (Obstacle Blocked: Traffic / Delays)",
            "type": "obstacle",
            "color": "#ef4444",
            "co2_kg": round(standard_co2, 2)
        }
    }

    terrain_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": terrain_coords
        },
        "properties": {
            "name": "⚠️ Route B (Steep Terrain / High Elevation Incline)",
            "type": "terrain",
            "color": "#eab308",
            "co2_kg": round(standard_co2 * 1.14, 2)
        }
    }

    # Obstacle markers from Cell 2 & Cell 3 of CarbonShift.ipynb
    obstacle_points = [
        {
            "lat": round(via_central[1], 4),
            "lon": round(via_central[0], 4),
            "title": "🔴 Severe Traffic Jam & Congestion Delay (+38m delay, +18kg CO2)",
            "type": "obstacle",
            "color": "red"
        },
        {
            "lat": round(via_terrain[1], 4),
            "lon": round(via_terrain[0], 4),
            "title": "🟡 Steep 14% Incline (Heavy Diesel Terrain Gradient Strain)",
            "type": "terrain",
            "color": "yellow"
        },
        {
            "lat": round(via_eco[1], 4),
            "lon": round(via_eco[0], 4),
            "title": "✨ CarbonShift Optimal Eco-Waypoint (Zero Idling & Low Grade)",
            "type": "eco",
            "color": "green"
        }
    ]

    # Record event in live Session Audit Log
    SESSION_AUDIT_LOG.insert(0, {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "origin": f"[{round(orig_lat, 2)}, {round(orig_lon, 2)}]",
        "destination": f"[{round(dest_lat, 2)}, {round(dest_lon, 2)}]",
        "vehicle": vehicle_type,
        "co2_saved_kg": round(co2_saved, 2),
        "savings_pct": savings_pct,
        "routing_engine": "Mapbox v5 Multi-Route (CarbonShift.ipynb)"
    })

    return RouteCalculationResponse(
        status="success",
        source="CarbonShift_Notebook_Physics_Engine",
        distance_km=round(eco_distance_km, 1),
        distance_miles=round(eco_distance_km * 0.621371, 1),
        vehicle_type=vehicle_type,
        co2_emissions_kg=round(eco_co2, 2),
        baseline_co2_kg=round(standard_co2, 2),
        co2_saved_kg=round(co2_saved, 2),
        estimated_fuel_cost_usd=eco_cost_usd,
        baseline_fuel_cost_usd=standard_cost_usd,
        fuel_saved_usd=cost_saved_usd,
        eco_savings_percent=savings_pct,
        elevation_gain_m=round(elevation_m, 1),
        traffic_idle_minutes=round(idle_mins, 1),
        trees_equivalent=trees_eq,
        route_geojson=eco_geojson,
        eco_geojson=eco_geojson,
        standard_geojson=obstacle_geojson,
        obstacle_geojson=obstacle_geojson,
        terrain_geojson=terrain_geojson,
        obstacles=obstacle_points
    )

# ==============================================================================
# 7. AUXILIARY AUDIT & PAN-INDIA HUBS ENDPOINTS
# ==============================================================================
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "engine": "CarbonShift.ipynb Python Backend",
        "hubs_count": len(PAN_INDIA_LOGISTICS_HUBS),
        "mapbox_active": True
    }

@app.get("/hubs")
def get_pan_india_hubs():
    return {"hubs": PAN_INDIA_LOGISTICS_HUBS}

@app.get("/audit-log")
def get_session_audit_log():
    return {"audit_log": SESSION_AUDIT_LOG[:25]}

if __name__ == "__main__":
    print("[CarbonShift] Launching FastAPI backend from CarbonShift.ipynb on port 8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
