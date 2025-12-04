import numpy as np
import math
from openrouteservice import convert
from geopy.distance import geodesic

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

def calcular_consumo_y_emisiones(potencia_electrica_w, potencia_combustion_kw, tiempos, speeds):
    """
    Calcula el consumo total y las emisiones equivalentes de ciclo de vida
    """
    # Calcular consumo eléctrico total (kWh)
    consumo_electrico_total = 0
    consumo_combustion_total = 0
    
    for i in range(len(potencia_electrica_w)):
        if i == 0:
            delta_t = tiempos[0] if tiempos[0] > 0 else 1.0
        else:
            delta_t = max(tiempos[i] - tiempos[i-1], 0.1)
        
        tiempo_horas = delta_t / 3600
        consumo_electrico_total += (potencia_electrica_w[i] / 1000) * tiempo_horas
        consumo_combustion_total += potencia_combustion_kw[i] * tiempo_horas
    
    # Calcular distancia total (km)
    distancia_total = 0
    for i in range(len(speeds)):
        if i == 0:
            delta_t = tiempos[0] if tiempos[0] > 0 else 1.0
        else:
            delta_t = max(tiempos[i] - tiempos[i-1], 0.1)
        vel_ms = speeds[i] / 3.6
        distancia_total += vel_ms * delta_t
    distancia_km = distancia_total / 1000
    
    # Factores de emisión equivalentes de ciclo de vida (gCO₂/km)
    factor_emision_electrico_gco2_km = 35  # Motocicleta eléctrica
    factor_emision_combustion_gco2_km = 70  # Motocicleta a combustión
    
    # Emisiones equivalentes de ciclo de vida (kg CO₂)
    emisiones_electrico_kg = (factor_emision_electrico_gco2_km * distancia_km) / 1000
    emisiones_combustion_kg = (factor_emision_combustion_gco2_km * distancia_km) / 1000
    
    # Conversión de energía de combustible a galones
    poder_calorifico_gasolina_kwh_galon = 33.7
    consumo_galones = consumo_combustion_total / poder_calorifico_gasolina_kwh_galon

    return {
        'consumo_electrico_kwh': consumo_electrico_total,
        'consumo_combustion_kwh': consumo_combustion_total,
        'consumo_galones': consumo_galones,
        'distancia_km': distancia_km,
        'emisiones_electrico_kg': emisiones_electrico_kg,
        'emisiones_combustion_kg': emisiones_combustion_kg,
        'factor_emision_electrico': factor_emision_electrico_gco2_km,
        'factor_emision_combustion': factor_emision_combustion_gco2_km
    }

# Unidades de metros y segundos 
def get_vel_azure(features,elevation_data):
    route = {
        "coords":[],
        "speeds":[],
        "slopes":[],
        "times":[]
        }
    
    total_time = 0
    total_distance = 0

    for feature in features:
        props = feature["properties"]
        steps = props.get("steps", [])

        for step in steps:
            start_idx, end_idx = step["routePathRange"]["range"]

            step_duration = props.get("durationInSeconds", 0)
            step_distance = props.get("distanceInMeters", 0)
            num_points = end_idx - start_idx

            if num_points <= 0:
                continue

            duration_per_point = step_duration / num_points
            distance_per_point = step_distance / num_points
            
            for i in range(num_points):
                idx = start_idx + i
                
                lng, lat, alt = elevation_data[idx]

                if len(route["coords"]) > 0:
                    prev_lng, prev_lat, prev_alt = route["coords"][-1]
                else:
                    prev_lng, prev_lat, prev_alt = lng, lat, alt

                horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters

                delta_alt = alt - prev_alt

                slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0

                speed_ms = (distance_per_point / duration_per_point) if duration_per_point != 0 else 0

                prev_alt = route["coords"][-1][2] if len(route["coords"]) > 0 else alt

                route["coords"].append([lng, lat, alt])
                route["speeds"].append(round(speed_ms, 2))
                route["slopes"].append(round(slope_deg, 2))
                route["times"].append(round(total_time, 2))

                total_time += duration_per_point
                total_distance += distance_per_point

                if idx == len(elevation_data)-2:
                    lng, lat, alt = elevation_data[-1]
                    delta_alt = alt - prev_alt
                    horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters
                    slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0

                    lng, lat, alt = elevation_data[-1]
                    route["coords"].append([lng, lat, alt])
                    route["speeds"].append(round((distance_per_point / duration_per_point), 2))
                    route["slopes"].append(round(slope_deg, 2))
                    route["times"].append(round(total_time, 2))
    return route

def get_vel(steps, elevation_data):
    route = {
        "coords": [],      # [lng, lat, alt] format
        "speeds": [],      # m/s
        "slopes": [],      # grados  
        "times": []    
    }

    total_time = 0
    total_distance = 0

    for step in steps:
        start_idx, end_idx = step["way_points"]
        step_duration = step["duration"]  
        step_distance = step["distance"]  
        num_points = end_idx - start_idx

        if num_points <= 0:
            continue

        duration_per_point = step_duration / num_points
        distance_per_point = step_distance / num_points

        for i in range(num_points):
            idx = start_idx + i
            
            if idx >= len(elevation_data):
                break
                
            lng, lat, alt = elevation_data[idx]

            if len(route["coords"]) > 0:
                prev_lng, prev_lat, prev_alt = route["coords"][-1]
            else:
                prev_lng, prev_lat, prev_alt = lng, lat, alt

            horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters

            delta_alt = alt - prev_alt

            slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0

            speed_ms = (distance_per_point / duration_per_point) if duration_per_point != 0 else 0

            route["coords"].append([lng, lat, alt])
            route["speeds"].append(round(speed_ms, 2))
            route["slopes"].append(round(slope_deg, 2))
            route["times"].append(round(total_time, 2))

            total_time += duration_per_point
            total_distance += distance_per_point

            if idx == len(elevation_data)-2:
                lng, lat, alt = elevation_data[-1]
                delta_alt = alt - prev_alt
                horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters
                slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0

                route["coords"].append([lng, lat, alt])
                route["speeds"].append(round(speed_ms, 2))
                route["slopes"].append(round(slope_deg, 2))
                route["times"].append(round(total_time, 2))

    return route