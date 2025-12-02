from moto import Moto
from utils import manage_segments
from petitions import _fetch_ors_route, _fetch_azure_route, _fecth_alt
import numpy as np

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

            # Fetch route to station + destino
            nueva_ruta = await route(
                coords=[current_pos, station_coord, destiny],
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
        "geometry": {
            "coordinates": [[lon, lat] for lon, lat, _ in moto.positions],
            "type": "LineString"
        },
        "properties": {
            "potencia": moto.power,
            "soc": moto.soc_history,
            "speeds": speeds,
            "map_city": city,
            # NUEVO: consumos totales de la moto
            "total_electric_kwh": moto.total_electric_kwh,
            "total_combustion_kwh": moto.total_combustion_kwh,
        },
        "summary": {
            "distance": moto.distance,
            "duration": moto.duration
        },
        "alternatives": [],
        # Cada punto ahora tiene energy_charged, charge_time_min, etc.
        "charge_points": moto.puntos_recarga_realizados
    }