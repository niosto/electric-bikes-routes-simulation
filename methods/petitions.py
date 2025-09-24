import requests
import polyline
import math
from geopy.distance import geodesic

# lon, lat format
def get_route(coords,api_key):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "coordinates": coords,
        "instructions": True,
        "elevation":True
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error elevación: {response.text}")
    
    data = response.json()
    return data


def get_alt(coordinates, api_key):
    url = "https://api.openrouteservice.org/elevation/line"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    # ORS espera formato lat, lon para ENCODED_POLYLINE
    geometry_latlng = [(lat, lng) for lng, lat in coordinates]

    payload = {
        "format_in": "encodedpolyline",
        "format_out": "geojson",
        "geometry": polyline.encode(geometry_latlng)
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Error elevación: {response.text}")
    data = response.json()
    return data['geometry']['coordinates']

# lon lat
def get_opt_route(coords,time,api_key):
    features = []
    for idx, (lon, lat) in enumerate(coords):
        point_type = "waypoint" if idx in (0, len(coords) - 1) else "viaWaypoint"
        features.append({
            "type": "Feature",
            "geometry": {
                "coordinates": [lon, lat],
                "type": "Point"
            },
            "properties": {
                "pointIndex": idx,
                "pointType": point_type
            }
        })
    date = "2025-09-01T" + time + "-05:00" 

    body = {
        "type": "FeatureCollection",
        "features": features,
        "optimizeRoute": "fastestWithTraffic",
        "routeOutputOptions": ["itinerary","routePath"],
        "maxRouteCount": 1,
        "travelMode": "driving",
        "departAt": date
    }

    url = "https://atlas.microsoft.com/route/directions"
    params = {"api-version": "2025-01-01"}

    response = requests.post(
        url,
        params=params,
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "subscription-key": api_key
        },
        json=body
    )
    response.raise_for_status()
    return response.json()

# Unidades de metros y segundos 
def get_vel_azure(features,elevation_data):
    route = {
        "coords":[],
        "speed_ms":[],
        "slope_deg":[],
        "time":[],
        "distance":[]
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
                route["speed_ms"].append(round(speed_ms, 2))
                route["slope_deg"].append(round(slope_deg, 2))
                route["time"].append(round(total_time, 2))
                route["distance"].append(round(total_distance, 2))

                total_time += duration_per_point
                total_distance += distance_per_point

                if idx == len(elevation_data)-2:
                    lng, lat, alt = elevation_data[-1]
                    delta_alt = alt - prev_alt
                    horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters
                    slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0

                    lng, lat, alt = elevation_data[-1]
                    route["coords"].append([lng, lat, alt])
                    route["speed_ms"].append(round((distance_per_point / duration_per_point), 2))
                    route["slope_deg"].append(round(slope_deg, 2))
                    route["time"].append(round(total_time, 2))
                    route["distance"].append(round(total_distance, 2))
    return route

def get_vel(steps, elevation_data):
    route = {
        "coords": [],        # [lng, lat, alt] format
        "speed_ms": [],      # Speed in m/s
        "slope_deg": [],     # Slope in degrees
        "time": [],          # Cumulative time in seconds
        "distance": []       # Cumulative distance in meters
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
            route["speed_ms"].append(round(speed_ms, 2))
            route["slope_deg"].append(round(slope_deg, 2))
            route["time"].append(round(total_time, 2))
            route["distance"].append(round(total_distance, 2))

            total_time += duration_per_point
            total_distance += distance_per_point

            if idx == len(elevation_data)-2:
                lng, lat, alt = elevation_data[-1]
                delta_alt = alt - prev_alt
                horiz_dist = geodesic((prev_lat, prev_lng), (lat, lng)).meters
                slope_deg = math.degrees(math.atan2(delta_alt, horiz_dist)) if horiz_dist != 0 else 0

                route["coords"].append([lng, lat, alt])
                route["speed_ms"].append(round(speed_ms, 2))
                route["slope_deg"].append(round(slope_deg, 2))
                route["time"].append(round(total_time, 2))
                route["distance"].append(round(total_distance, 2))

    return route
