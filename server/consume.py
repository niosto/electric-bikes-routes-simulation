from moto import Moto
from petitions import get_vel, get_opt_route, get_vel_azure, get_alt
from ors_routes import _fetch_ors_route, _to2d

def manage_segments(rutas, traffic):
    rutas_moto = []
    if(not traffic):
        for segment in rutas["properties"]["segments"]:
            data = get_vel(segment["steps"], rutas["geometry"]["coordinates"])
            data["duration"] = segment["duration"]
            data["distance"] = segment["distance"]
            rutas_moto.append(data)
    return rutas_moto

async def fetch_routes(coords, token, traffic, client, profile):
    raw_route = []
    if(traffic):
        for i in range(len(coords)-1):
            coord = [coords[i],coords[i+1]]
            route_data = get_opt_route(coord, "08:00:00", token)
            route_data["features"][-1]["geometry"]["coordinates"][0] = get_alt(route_data["features"][-1]["geometry"]["coordinates"][0], token)
            raw_route.append(route_data)
    else:
        raw_route = await _fetch_ors_route(
                    client, token, profile, coords,
                    steps=True, geometries="geojson", exclude=[]
                )
    return raw_route

async def moto_consume(coords, estaciones, nombre, client, token, profile, traffic):
    raw_route = fetch_routes(coords, traffic)
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

            raw_route = []
            if(not traffic):
                # Fetch route to station
                raw_route = await _fetch_ors_route(
                    client, token, profile, [current_pos, station_coord, destiny],
                    steps=True, geometries="geojson", exclude=[]
                )
            else:
                raw_route = await 

            new_route = manage_segments(raw_route)

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
