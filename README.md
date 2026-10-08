# 🌿 CarbonShift — Intelligent Commercial Fleet Decarbonization Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green.svg?style=flat&logo=node.js)](https://nodejs.org)
[![Leaflet](https://img.shields.io/badge/Leaflet-1.9.4-199900.svg?style=flat&logo=leaflet)](https://leafletjs.com)
[![Mapbox](https://img.shields.io/badge/Mapbox-Directions%20API-000000.svg?style=flat&logo=mapbox)](https://mapbox.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CarbonShift** is an enterprise-grade commercial freight decarbonization platform that optimizes shipping routes, forecasts gradient potential energy, avoids congestion idling, and delivers real-time ESG compliance metrics across Pan-India logistics corridors.

The platform pairs a **Python physics engine** (derived from [`CarbonShift.ipynb`](CarbonShift.ipynb)) with an interactive **Leaflet + Mapbox high-definition routing workspace**, featuring multi-page separation, real-time geocoding autocomplete, and live telemetry synchronization.

---

## 🗺️ Tri-Route Intelligence Engine

CarbonShift computes and renders three distinct route topologies for every dispatch request:

```
                  ┌───────────────────────────────────────────────┐
                  │ 🔴 Route A: Direct Path (Obstacle Jammed)     │
                  │   - Heavy traffic delay (+38 mins)            │
                  │   - Urban idling spike (+18.4 kg CO₂)         │
                  └───────────────────────────────────────────────┘
                                         ▲
Origin (Hub A) ──────────────────────────┼──────────────────────────► Destination (Hub B)
                                         ▼
                  ┌───────────────────────────────────────────────┐
                  │ 🟡 Route B: Mountain Pass (Steep Terrain)     │
                  │   - +14% slope incline hazard                 │
                  │   - Heavy torque strain on diesel powertrains │
                  └───────────────────────────────────────────────┘
                                         ▼
                  ┌───────────────────────────────────────────────┐
                  │ 🟢 Route C: CarbonShift Optimal Eco-Route     │
                  │   - Bypasses grade hazards & urban idling     │
                  │   - 21.9% average lifecycle CO₂ abatement     │
                  └───────────────────────────────────────────────┘
```

1. **🔴 Red Route — Obstacles & Traffic Congestion**:
   - Highlighting direct highway corridors impacted by severe traffic jams, roadblocks, or construction delays.
   - Pinned with interactive obstacle warning markers (`🚫 Severe Traffic Jam & Delay`).
2. **🟡 Yellow Route — Terrain & Elevated Incline**:
   - Traces topographically complex routes characterized by steep mountain grades (+14% incline).
   - Accurately computes elevation potential energy penalties for commercial diesel loads.
3. **🟢 Green Route — CarbonShift Optimal Eco-Route**:
   - Road-snapped dynamic bypass engineered for minimum fuel burn and zero idling.
   - Rendered with an emerald glow casing and verified with GLEC Framework v3 compliance.

---

## 🌟 Multi-Page Application Architecture

Each platform function lives on its own dedicated page with seamless global navigation:

| Page | File | Description |
| :--- | :--- | :--- |
| **Route Optimizer** | [`optimizer.html`](optimizer.html) | Expansive screen-dominant HD map (760px), Pan-India Mapbox autocomplete, live telemetry sidebar, and tri-route rendering. |
| **Platform Home** | [`index.html`](index.html) | DriveNest-inspired executive showcase with hero calculator, fleet features, and platform overview. |
| **Fleet Analytics** | [`dashboard.html`](dashboard.html) | Interactive Chart.js analytics: CO₂ abatement trends, OpEx cost breakdowns, and fleet asset benchmarks. |
| **ESG Compliance** | [`reports.html`](reports.html) | Scope 1, 2, and 3 emissions accounting, CSRD / SEC audit readiness scorecards, and CSV trip logs export. |
| **Carrier Portal** | [`login.html`](login.html) | Commercial fleet login with USDOT verification and instant 1-click enterprise demo profiles. |

---

## 🛠️ Technology Stack

- **Backend**: Python 3, FastAPI, Uvicorn, Pydantic, Requests.
- **Physics Engine**: GLEC Framework v3, EPA SmartWay factors, Hugging Face vehicle & charging datasets (`CarbonShift.ipynb`).
- **Geocoding & Routing**: Mapbox Driving Directions v5 API, Mapbox Geocoding Autocomplete.
- **Frontend Mapping**: Leaflet.js with Google Maps HD Layers (Roadmap, Satellite, Hybrid, Terrain).
- **Charts & Telemetry**: Chart.js for corporate emissions modeling.
- **Server**: Node.js static server & reverse proxy (`server.js`).

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/CarbonShift.git
cd CarbonShift
```

### 2. Set Up the Python Backend
Install dependencies:
```bash
pip install -r requirements.txt
```

Launch the FastAPI engine (runs on port `8000`):
```bash
python backend.py
```
> The API will be available at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.

### 3. Launch the Web Platform
In a separate terminal, start the Node server (runs on port `3000`):
```bash
node server.js
```

### 4. Access the Application
Open your web browser at:
- **Route Optimizer Workspace**: [http://localhost:3000/optimizer.html](http://localhost:3000/optimizer.html)
- **Platform Home**: [http://localhost:3000/index.html](http://localhost:3000/index.html)
- **Fleet Analytics Dashboard**: [http://localhost:3000/dashboard.html](http://localhost:3000/dashboard.html)
- **ESG Sustainability Reports**: [http://localhost:3000/reports.html](http://localhost:3000/reports.html)
- **Carrier Portal**: [http://localhost:3000/login.html](http://localhost:3000/login.html)

---

## 📡 API Specification

### `POST /calculate-route`
Calculates optimal corridor metrics, physics parameters, and GeoJSON features for all three routes.

**Request Body**:
```json
{
  "origin_lat": 18.9499,
  "origin_lon": 72.9510,
  "dest_lat": 18.7600,
  "dest_lon": 73.8500,
  "vehicle_type": "Heavy-Duty Diesel Truck",
  "elevation_gain_m": 560.0,
  "traffic_idle_minutes": 35.0
}
```

**Response Payload**:
```json
{
  "status": "success",
  "source": "CarbonShift_Notebook_Physics_Engine",
  "distance_km": 142.6,
  "vehicle_type": "Heavy-Duty Diesel Truck",
  "co2_emissions_kg": 311.07,
  "baseline_co2_kg": 1172.33,
  "co2_saved_kg": 861.26,
  "eco_savings_percent": 73.5,
  "trees_equivalent": 38.8,
  "eco_geojson": { "type": "Feature", "properties": { "color": "#16a34a" }, ... },
  "obstacle_geojson": { "type": "Feature", "properties": { "color": "#ef4444" }, ... },
  "terrain_geojson": { "type": "Feature", "properties": { "color": "#eab308" }, ... },
  "obstacles": [
    { "lat": 18.87, "lon": 73.41, "title": "🔴 Severe Traffic Jam & Delay", "type": "obstacle" },
    { "lat": 18.89, "lon": 73.45, "title": "🟡 Steep 14% Incline", "type": "terrain" },
    { "lat": 18.83, "lon": 73.35, "title": "✨ CarbonShift Optimal Eco-Waypoint", "type": "eco" }
  ]
}
```

---

## 📁 Project Directory Structure

```
CarbonShift/
├── assets/                  # Brand assets & visual templates
│   ├── carbonshift_splash.jpg
│   └── drivenest_template.png
├── css/
│   └── styles.css           # Custom design tokens, glassmorphism, animations
├── js/
│   ├── api.js               # API client, offline fallbacks, clipboard utilities
│   ├── app.js               # UI controller, event handlers, splash screen
│   ├── auth.js              # Enterprise authentication & demo accounts
│   ├── charts.js            # Chart.js analytics controllers
│   ├── geocoder.js          # Mapbox India geocoding & autocomplete engine
│   ├── map.js               # Leaflet Tri-Route engine & hazard pins
│   └── reports.js           # ESG reporting, CSV export, audit logs
├── CarbonShift.ipynb        # Jupyter Notebook with core physics models & training data
├── backend.py               # Standalone FastAPI physics engine
├── server.js                # Node static server with backend reverse proxy
├── index.html               # Platform Home showcase
├── optimizer.html           # Dedicated Route Optimizer workspace (large map)
├── dashboard.html           # Dedicated Fleet Analytics dashboard
├── reports.html             # Dedicated ESG compliance reports
├── login.html               # Commercial Carrier Enterprise Portal
├── package.json             # Node configuration & scripts
├── requirements.txt         # Python dependencies
├── .gitignore               # Ignored build artifacts & secrets
├── LICENSE                  # MIT License
└── README.md                # Platform documentation
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
