import os
from typing import List, Dict, Any, Tuple
from fastapi import FastAPI, HTTPException, Path, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from ors_routes import _fetch_ors_route, _to2d

from dotenv import load_dotenv
from consume import moto_consume
import httpx
import json

load_dotenv()

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")]
ORS_TOKEN = os.getenv("ORS_TOKEN", "")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(title="Multi rutas ORS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================== MODELOS (JSON simple) ===================
class Waypoint(BaseModel):
    coordinates: List[float]  # [lng, lat] o [lng, lat, alt]

class VehicleInput(BaseModel):
    vehicle_id: str
    waypoints: List[Waypoint] = Field(default_factory=list)

class Options(BaseModel):
    profile: str = "driving"
    alternatives: bool = False
    steps: bool = True
    geometries: str = "geojson"
    exclude: List[str] = Field(default_factory=list)
    # Alternativas ORS
    alt_count: int = 3
    alt_share: float = 0.6
    alt_weight: float = 1.4

class RoutesRequest(BaseModel):
    options: Options
    vehicles: List[VehicleInput]

# =================== SALUD ===================
@app.get("/health")
def health():
    return {"ok": True, "provider": "ors", "has_token": bool(ORS_TOKEN)}

@app.get("/estaciones")
async def estaciones():
    try:
        with open("resources/estaciones_med.json","r") as f:
            estaciones_med = json.load(f)
            return estaciones_med
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error: {e}")

# =================== RUTAS: JSON simple ===================
@app.post("/routes")
async def routes(body: RoutesRequest):
    idx = 1

    if not ORS_TOKEN:
        raise HTTPException(status_code=500, detail="ORS_TOKEN no configurado en .env")
    
    out: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:

        for v in body.vehicles:
            if len(v.waypoints) < 2:
                continue
            coords = _to2d([wp.coordinates for wp in v.waypoints])  # 👈 2D aquí también
            if len(coords) < 2:
                continue
            try:
                r = await _fetch_ors_route(
                    client=client,
                    token=ORS_TOKEN,
                    profile_key=body.options.profile,
                    coords=coords,
                    steps=body.options.steps,
                    geometries=body.options.geometries,
                    exclude=body.options.exclude,
                    want_alternatives=body.options.alternatives,
                    alt_count=body.options.alt_count,
                    alt_share=body.options.alt_share,
                    alt_weight=body.options.alt_weight,
                )

                with open("resources/estaciones_med.json","r") as f:
                    estaciones_med = json.load(f)

                data = await moto_consume(r, estaciones_med, f"moto-{idx}", client, ORS_TOKEN, body.options.profile)

            except httpx.RequestError as e:
                raise HTTPException(status_code=502, detail=f"Error de red ORS: {e!s}")
            
            idx += 1

            out.append({"vehicle_id": v.vehicle_id, **data})

    with open("resources/ej_out.json","w")as f:
        json.dump({"routes": out},f,indent=2)

    return {"routes": out}

# =================== RUTAS: GeoJSON FeatureCollection ===================
@app.post("/routes/geojson")
async def routes_geojson(request: Request):
    if not ORS_TOKEN:
        raise HTTPException(status_code=500, detail="ORS_TOKEN no configurado en .env")

    body = await request.json()
    if body.get("type") != "FeatureCollection" or "features" not in body:
        raise HTTPException(status_code=400, detail="Se esperaba un FeatureCollection GeoJSON")

    profile = (request.query_params.get("profile") or "driving").lower()
    steps = (request.query_params.get("steps") or "true").lower() == "true"
    geometries = request.query_params.get("geometries") or "geojson"
    # Si quieres excluir, parsea ?exclude=toll,motorway
    exclude: List[str] = []

    want_alts = (request.query_params.get("alternatives") or "false").lower() == "true"
    alt_count = int(request.query_params.get("alt_count") or 3)
    alt_share = float(request.query_params.get("alt_share") or 0.6)
    alt_weight = float(request.query_params.get("alt_weight") or 1.4)

    features = body["features"]
    out: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        idx = 1
        for feat in features:
            geom = (feat or {}).get("geometry") or {}
            if geom.get("type") != "LineString":
                continue
            coords = _to2d(geom.get("coordinates") or [])  # 2D
            if len(coords) < 2:
                continue

            vehicle_id = ((feat.get("properties") or {}).get("vehicle_id")) or f"moto-{idx}"
            idx += 1

            try:
                r = await _fetch_ors_route(
                    client=client,
                    token=ORS_TOKEN,
                    profile_key=profile,
                    coords=coords,
                    steps=steps,
                    geometries=geometries,
                    exclude=exclude,
                    want_alternatives=want_alts,
                    alt_count=alt_count,
                    alt_share=alt_share,
                    alt_weight=alt_weight,
                )
            except httpx.RequestError as e:
                raise HTTPException(status_code=502, detail=f"Error de red ORS: {e!s}")

            out.append({"vehicle_id": vehicle_id, **r})

    return {"routes": out}

# =================== GEOJSON echo/validador ===================
@app.post("/geojson")
async def geojson_echo(req: Request):
    data = await req.json()
    if data.get("type") != "FeatureCollection":
        raise HTTPException(status_code=400, detail="Se esperaba FeatureCollection")
    return {"ok": True, "received": data}

# =================== TILE PROXY ===================
@app.get("/tiles/carto/{z}/{x}/{y}.png")
async def tile_carto(
    z: int = Path(..., ge=0, le=22),
    x: int = Path(..., ge=0),
    y: str = Path(...),
):
    retina_suffix = ""
    if "@2x" in y:
        y_clean = y.replace("@2x", "")
        retina_suffix = "@2x"
    else:
        y_clean = y

    url = f"https://{{s}}.basemaps.cartocdn.com/light_all/{z}/{x}/{y_clean}{retina_suffix}.png"
    subdomains = ["a", "b", "c", "d"]
    s = subdomains[(x + z) % len(subdomains)]
    url = url.replace("{s}", s)

    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(url)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Error trayendo tile Carto: {e!s}")

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=f"Carto devolvió {r.status_code}")

    headers = {"Content-Type": "image/png", "Cache-Control": "public, max-age=86400"}
    return Response(content=r.content, headers=headers, media_type="image/png")

@app.get("/tiles/osm/{z}/{x}/{y}.png")
async def tile_osm(
    z: int = Path(..., ge=0, le=22),
    x: int = Path(..., ge=0),
    y: int = Path(..., ge=0),
):
    url = f"https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            r = await client.get(url)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Error trayendo tile OSM: {e!s}")

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=f"OSM devolvió {r.status_code}")

    headers = {"Content-Type": "image/png", "Cache-Control": "public, max-age=86400"}
    return Response(content=r.content, headers=headers, media_type="image/png")