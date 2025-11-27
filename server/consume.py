from moto import Moto
from utils import get_vel, get_vel_azure
from petitions import _fetch_ors_route, _to2d, _fetch_azure_route, _fecth_alt
import numpy as np

def preprocesar_vectores(velocidades, pendientes, tiempos, coordenadas, puntos_intermedios=10):
    n_original = len(velocidades)
    if(n_original < 2):
        return velocidades, pendientes, tiempos, coordenadas
    n_nuevo = n_original + (n_original - 1) * puntos_intermedios
    
    x_original = np.arange(n_original)
    x_nuevo = np.linspace(0, n_original - 1, n_nuevo)
    
    velocidades_interp = np.interp(x_nuevo, x_original, velocidades).tolist()
    pendientes_interp = np.interp(x_nuevo, x_original, pendientes).tolist()
    tiempos_interp = np.interp(x_nuevo, x_original, tiempos).tolist()
    
    coords_interp = []
    for i in range(3):
        valores = [coord[i] for coord in coordenadas]
        valores_interp = np.interp(x_nuevo, x_original, valores)
        coords_interp.append(valores_interp.tolist())
    
    coordenadas_interp = [[coords_interp[0][i], coords_interp[1][i], coords_interp[2][i]] for i in range(n_nuevo)]
    
    return velocidades_interp, pendientes_interp, tiempos_interp, coordenadas_interp

def manage_segments(rutas, traffic, elevation=None):
    rutas_moto = []

    if traffic:
        rutas = rutas["features"]

        data = get_vel_azure(rutas, elevation)
        data["distance"] = rutas[-1]["properties"]["distanceInMeters"]
        data["duration"] = rutas[-1]["properties"]["durationInSeconds"]

        vel_interp, pend_interp, time_interp, coords_interp = preprocesar_vectores(
                data["speeds"], data["slopes"], data["times"], data["coords"], puntos_intermedios=2)
        data["speeds"] = vel_interp
        data["slopes"] = pend_interp
        data["times"] = time_interp
        data["coords"] = coords_interp

        rutas_moto = data
    else:
        for segment in rutas["properties"]["segments"]:
            data = get_vel(segment["steps"], rutas["geometry"]["coordinates"])

            data["duration"] = segment["duration"]
            data["distance"] = segment["distance"]
            vel_interp, pend_interp, time_interp, coords_interp = preprocesar_vectores(
                data["speeds"], data["slopes"], data["times"], data["coords"], puntos_intermedios=2)

            data["speeds"] = vel_interp
            data["slopes"] = pend_interp
            data["times"] = time_interp
            data["coords"] = coords_interp
            rutas_moto.append(data)
    return rutas_moto

async def route(coords, traffic, ors_token, azure_token, client):
    rutas_moto = []
    if traffic:
        for i in range(len(coords)-1):
            ruta_azure = await _fetch_azure_route(
                client=client,
                token=azure_token,
                coords=[coords[i], coords[i+1]]
            )

            ruta_alt = await _fecth_alt(
                client=client,
                token=ors_token,
                coords=ruta_azure["features"][-1]["geometry"]["coordinates"][0]
            )

            rutas = manage_segments(
                rutas=ruta_azure,
                traffic=traffic,
                elevation=ruta_alt
            )

            rutas_moto.append(rutas)

    else:
        ors_route = await _fetch_ors_route(
                client, ors_token, "driving", coords,
                steps=True, geometries="geojson", exclude=[]
            )
        
        rutas_moto = manage_segments(
            rutas= ors_route,
            traffic=traffic,
        )
        
    return rutas_moto

async def moto_consume(coords, estaciones, nombre, client, ors_token, azure_token, profile, city = "med", traffic=False):

    rutas = await route(
        coords=coords,
        traffic=traffic,
        ors_token=ors_token,
        azure_token=azure_token,
        client=client
    )

    moto = Moto(nombre, rutas, estaciones, hybrid_cont=0.5)
    step_result = moto.avanzar_paso()

    while step_result != 0:
        if step_result == 3:
            # Battery low: reroute to nearest charging station
            current_pos = moto.route_data[moto.idx]["coords"][moto.idx_ruta][:2]

            idx_est = moto.nearest_station(current_pos)

            station_coord = estaciones["coords"][idx_est]
            
            destiny = moto.route_data[moto.idx]["coords"][-1][:2]

            moto.add_charge_point(idx_est, current_pos)

            # Fetch route to station
            nueva_ruta = await route(
                coords=[current_pos,station_coord,destiny],
                traffic=traffic,
                ors_token=ors_token,
                azure_token=azure_token,
                client=client
            )

            moto.change_route(nueva_ruta)

        step_result = moto.avanzar_paso()
        
    speeds = []
    for ruta in moto.route_data:
        speeds.extend(ruta["speeds"])

    return {
        "geometry":{
            "coordinates": [[lon, lat] for lon,lat,_ in moto.positions],
            "type":"LineString"
        },
        "properties": {
            "potencia": moto.power,
            "soc": moto.soc_history,
            "speeds": speeds,
            "map_city": city,
        },
        "summary":{
            "distance":moto.distance,
            "duration":moto.duration
        },
        "alternatives":[],
        "charge_points": moto.puntos_recarga_realizados
    }
