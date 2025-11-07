from moto import Moto
from petitions import get_vel
from ors_routes import _fetch_ors_route, _to2d


def manage_segments(rutas):
    rutas_moto = []
    for segment in rutas["properties"]["segments"]:
        data = get_vel(segment["steps"], rutas["geometry"]["coordinates"])
        data["duration"] = segment["duration"]
        data["distance"] = segment["distance"]
        rutas_moto.append(data)
    return rutas_moto

async def moto_consume(rutas, estaciones, nombre, client, token, profile):
    
    rutas_moto = manage_segments(rutas) 
    moto = Moto(nombre, rutas_moto, estaciones)
    step_result = moto.avanzar_paso()

    while step_result != 0:
        if step_result == 3:
            # Battery low: reroute to nearest charging station
            current_pos = moto.route_data[moto.idx]["coords"][moto.idx_route][:2]

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

    return {
        "geometry":{
            "coordinates": [[lon, lat] for lon,lat,_ in moto.positions],
            "type":"LineString"
        },
        "properties":{
            "potencia":moto.power,
            "soc": moto.soc_history,
        },
        "summary":{
            "distance":moto.distance,
            "duration":moto.duration
        },
        "alternatives":[],
        "charge_points": moto.puntos_recarga_realizados
    }
