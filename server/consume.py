from moto import Moto
from petitions import get_vel
from ors_routes import _fetch_ors_route, _to2d
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

def manage_segments(rutas):
    rutas_moto = []
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

async def moto_consume(rutas, estaciones, nombre, client, token, profile, city = "med"):
    rutas_moto = manage_segments(rutas) 
    moto = Moto(nombre, rutas_moto, estaciones, hybrid_cont=0.5)
    step_result = moto.avanzar_paso()

    while step_result != 0:
        if step_result == 3:
            print("Cargar")
            # Battery low: reroute to nearest charging station
            current_pos = moto.route_data[moto.idx]["coords"][moto.idx_ruta][:2]

            idx_est = moto.nearest_station(current_pos)

            station_coord = estaciones["coords"][idx_est]
            
            destiny = moto.route_data[moto.idx]["coords"][-1][:2]

            moto.add_charge_point(idx_est, current_pos)

            # Fetch route to station
            new_ors_route = await _fetch_ors_route(
                client, token, profile, [current_pos, station_coord, destiny],
                steps=True, geometries="geojson", exclude=[]
            )

            new_route = manage_segments(new_ors_route)

            moto.change_route(new_route)

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
