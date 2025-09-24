import pickle
import pandas as pd
import numpy as np
import webbrowser
import math
from geopy.distance import geodesic
import folium
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

def bike_model_particle(hybrid_cont, speeds, slopes, positions=None, recarga_locations=None, umbral_energia=500, tiempo_recarga=60):
    # Se carga el parámetro del vehículo (eléctrico o híbrido)
    if hybrid_cont == 0:
        from HybridBikeConsumptionModel.parameters_electric import HEV
    else:
        from HybridBikeConsumptionModel.parameters_hybrid import HEV
    hev = HEV()
    
    # Se definen los puntos de recarga si no se pasan sus coordenadas
    if recarga_locations is None:
        recarga_locations = [
            ((6.197639, -75.5781), "EAFIT"),
            ((6.197860, -75.5597), "El tesoro"),
            ((6.186745, -75.5620), "Complex los Balsos")
        ]
    recarga_idx = 0  # Índice utilizado cuando no se tengan posiciones dinámicas

    last_vel = 0
    State_bater = 700  # Capacidad inicial de la batería (Wh)
    Energy = []        # Se almacena el estado de carga (SOC) de la batería
    Energy1 = []       # Se almacena el consumo eléctrico en Wh
    combus = []        # Se almacena el consumo de combustible en galones
    combus2 = []       # Se almacena el consumo de combustible en Wh
    E_TOTAL = []       # Se almacena la potencia total consumida

    # Variables para simular el proceso de recarga
    en_recarga = False           # Indica si se está recargando
    tiempo_en_recarga = 0        # Contador de tiempo durante la recarga
    ruta_actual = 0              # Índice en que se detuvo la moto
    charging_station_idx = None  # Índice de la estación de recarga elegida

    recharges = []  # Lista para almacenar los puntos donde se realizó la recarga

    # Recorrido de cada instante de la simulación a partir de la lista "speeds"
    for i in range(len(speeds)):
        # Si la batería es inferior al umbral y aún no se ha iniciado la recarga
        if State_bater < umbral_energia and not en_recarga:
            # Si se dispone de posiciones dinámicas, se toma la posición de este instante
            if positions is not None:
                current_pos = positions[i] if i < len(positions) else positions[-1]
                distances = [geodesic(current_pos, station[0]).meters for station in recarga_locations]
                charging_station_idx = distances.index(min(distances))
            else:
                charging_station_idx = recarga_idx
                
            station_coord, station_name = recarga_locations[charging_station_idx]
            print(f"¡Batería baja de umbral! Redirigiendo a {station_name}")
            # Almacenar el punto de recarga para graficarlo
            recharges.append(station_coord)
            en_recarga = True
            ruta_actual = i
            speeds[i] = 0
            slopes[i] = 0

        # Simulación del tiempo de recarga
        if en_recarga:
            tiempo_en_recarga += 1
            if tiempo_en_recarga >= tiempo_recarga:
                en_recarga = False
                tiempo_en_recarga = 0
                State_bater = 700  # La batería se recarga completamente
                station_coord, station_name = recarga_locations[charging_station_idx]
                print(f"¡Moto recargada en {station_name}! Retomando la ruta en la posición {ruta_actual + 1}")
                speeds[i:] = speeds[ruta_actual:]
                slopes[i:] = slopes[ruta_actual:]
                if positions is None:
                    recarga_idx = (recarga_idx + 1) % len(recarga_locations)

        # Cálculos físicos de la simulación
        vel = speeds[i] / 3.6  # Conversión km/h a m/s
        theta = slopes[i] * math.pi / 180  # Conversión grados a radianes
        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * np.cos(theta)
        fg = hev.Ambient.g * hev.Chassis.m * np.sin(theta)
        delta_v = vel - last_vel
        f_inertia = hev.Chassis.m * delta_v / 1
        fres = faero + froll + fg + f_inertia
        p_e = vel * fres
        p_m = (fres * hev.Wheel.rw) * (vel / hev.Wheel.rw)
        p_eb = p_m * (1 - hybrid_cont) / 0.7
        p_cn = p_m * (hybrid_cont) / 0.2
        if p_cn <= 0:
            p_cn = 0

        last_vel = vel
        pow_consumption = p_eb / 3600
        pcn_consumption = p_cn / 3600
        result = pow_consumption
        result1 = State_bater - pow_consumption
        result2 = pcn_consumption / 36718.50158230244
        result3 = pcn_consumption
        Energy.append(result1)
        Energy1.append(result)
        combus.append(result2)
        combus2.append(result3)
        E_TOTAL.append(pow_consumption + pcn_consumption)

        State_bater = result1
        if State_bater > 700:
            State_bater = 700

    return State_bater, combus, combus2, E_TOTAL, Energy, Energy1, recharges


# Función para interpolar entre dos puntos (origen y destino)
def interpolate_position(origin, destination, t):
    lat = origin[0] + t * (destination[0] - origin[0])
    lon = origin[1] + t * (destination[1] - origin[1])
    return (lat, lon)

# Se definen las ubicaciones usadas en el mapa final
ubic = [
    ((6.199845, -75.5628), "Donde Lucho"),
    ((6.197639, -75.5781), "EAFIT"),
    ((6.197860, -75.5597), "Tesoro"),
    ((6.199807, -75.5628), "D1 los parra"),
    ((6.197172, -75.5746), "Santa Fe"),
    ((6.199927, -75.5761), "Oviedo"),
    ((6.181040, -75.5688), "San Lucas"),
    ((6.186745, -75.5620), "Complex Balsos"),
    ((6.179232, -75.5878), "Mc Donalds Las Vegas"),
    ((6.186679, -75.5822), "Jumbo Las Vegas"),
    ((6.183508, -75.5794), "Euro La Frontera"),
    ((6.208052, -75.5636), "Vizcaya"),
    ((6.197014, -75.5634), "Edificio Villada"),
    ((6.196703, -75.5670), "Urbanizacion Villas de la loma"),
    ((6.190933, -75.5727), "Edificio Menta"),
    ((6.196362, -75.5766), "Edificio los Esteros"),
    ((6.185698, -75.5810), "Edificio Pinares de Zuniga"),
    ((6.180684, -75.5770), "Edificio Zu"),
    ((6.182890, -75.5585), "Edificio DuVille"),
    ((6.182330, -75.5622), "Urbanizacion Gualcala"),
    ((6.183127, -75.5718), "Edificio Compostela"),
    ((6.192652, -75.5813), "Edificio GP"),
    ((6.187564, -75.5800), "Edificio San Gabriel"),
    ((6.196830, -75.5699), "Edificio Spiga"),
    ((6.203083, -75.5709), "Urbanizacion Plaza de Alejandria"),
    ((6.202794, -75.5749), "Edificio Vytra"),
    ((6.199976, -75.5687), "Edifico Montemayor"),
    ((6.199811, -75.5664), "Edificios altos de parral"),
    ((6.200929, -75.5584), "Edificio San Francisco"),
    ((6.195713, -75.5556), "Edificio Santangelo"),
    ((6.191324, -75.5599), "Urbanizacion Cibeles"),
    ((6.190638, -75.5642), "Edificio Ryo")
]

# Lectura del archivo que contiene datos de velocidades y pendientes
ruta_archivo = "speed_slope_smooth.pkl"
data = pd.read_pickle(ruta_archivo)
records = []
for origin, row in data.iterrows():
    for destination, values in row.items():
        if isinstance(values, dict) and 'speeds' in values and 'slopes' in values:
            records.append({
                'from_lat_lon': origin,
                'to_lat_lon': destination,
                'speeds': values['speeds'],
                'slopes': values['slopes']
            })
df_resultado = pd.DataFrame(records)

# Se seleccionan las primeras 1032 rutas ordenadas
df = df_resultado[0:32]

# Generación del bounding box a partir de todas las coordenadas
all_from = list(df["from_lat_lon"])
all_to   = list(df["to_lat_lon"])
all_coords = all_from + all_to
all_lats = [c[0] for c in all_coords]
all_lons = [c[1] for c in all_coords]
north = max(all_lats)
south = min(all_lats)
east  = max(all_lons)
west  = min(all_lons)
bbox_tuple = (west, south, east, north)
print(f"BBox => west={west}, south={south}, east={east}, north={north}")

# Descarga del grafo de red vial del área definida
G = ox.graph_from_bbox(
    bbox_tuple, 
    network_type='drive',
    simplify=True,
    retain_all=True
)
print("Descargado G con", len(G.nodes()), "nodos y", len(G.edges()), "aristas")

all_speeds = []
all_slopes = []

# Creación de un mapa Folium centrado en el primer origen
center_map = df.iloc[0]["from_lat_lon"]
m = folium.Map(location=center_map, zoom_start=14)

print("Revisando las rutas seleccionadas:")
for i, row in df.iterrows():
    print(f"Ruta #{i} - Origen: {row['from_lat_lon']} - Destino: {row['to_lat_lon']}")

# Determinación de rutas válidas, acumulación de speeds y slopes, y trazado en el mapa
valid_count = 0
invalid_count = 0
# Se almacenarán posiciones interpoladas para obtener la ubicación dinámica
dynamic_positions = []
for i in range(len(df)):
    row = df.iloc[i]
    from_coords = row["from_lat_lon"]
    to_coords = row["to_lat_lon"]
    sp = row["speeds"]  # Se asume que es una lista
    sl = row["slopes"]
    orig_node = ox.distance.nearest_nodes(G, from_coords[1], from_coords[0])
    dest_node = ox.distance.nearest_nodes(G, to_coords[1], to_coords[0])
    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight="length")
    except nx.NetworkXNoPath:
        print(f"No path para ruta #{i} => {from_coords} -> {to_coords}. Omitimos.")
        invalid_count += 1
        continue
    valid_count += 1
    all_speeds.extend(sp)
    all_slopes.extend(sl)
    route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]
    folium.Marker(from_coords, tooltip=f"Origen {i}", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(to_coords, tooltip=f"Destino {i}", icon=folium.Icon(color="red")).add_to(m)
    folium.PolyLine(route_coords, color="blue", weight=4).add_to(m)
    
    # Generación de posiciones interpoladas para cada ruta
    n_points = len(sp)
    for j in range(n_points):
        t = j / (n_points - 1) if n_points > 1 else 0
        dynamic_positions.append(interpolate_position(from_coords, to_coords, t))

print(f"Rutas válidas: {valid_count}")
print(f"Rutas inválidas: {invalid_count}")

m.save("rutas.html")
print("Se guardó rutas.html")
try:
    webbrowser.open("rutas.html")
except:
    pass

# Se asigna la lista de posiciones con las posiciones dinámicas interpoladas
positions = dynamic_positions

if len(all_speeds) == 0:
    print("Ninguna de las rutas tenía un camino en el grafo, no hay datos.")
else:
    State_bat, combus, combus2, E_TOTAL, Energy, Energy1, recharges = bike_model_particle(
        hybrid_cont=0,
        speeds=all_speeds,
        slopes=all_slopes,
        positions=positions  # Uso de posiciones dinámicas para el cálculo de recarga
    )

    # Graficar las rutas y luego agregar los marcadores para los puntos de recarga
    plt.figure(figsize=(8, 4))
    plt.plot(all_speeds, label="Velocidad [km/h]")
    plt.title("Velocidad")
    plt.xlabel("Índice")
    plt.ylabel("km/h")
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.figure(figsize=(8, 4))
    plt.plot(all_slopes, label="Pendiente [°]", color="orange")
    plt.title("Pendiente")
    plt.xlabel("Índice")
    plt.ylabel("Grados")
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.figure(figsize=(8, 4))
    plt.plot(combus, label="Combustible (gal)")
    plt.plot(combus2, label="Combustible (Wh)")
    plt.title("Consumo Combustible")
    plt.xlabel("Índice")
    plt.ylabel("Consumo")
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.figure(figsize=(8, 4))
    plt.plot(Energy, label="SOC Batería")
    plt.title("Estado de Carga")
    plt.xlabel("Índice")
    plt.ylabel("Wh")
    plt.grid(True)
    plt.legend()
    plt.show()

    plt.figure(figsize=(8, 4))
    plt.plot(Energy1, label="Consumo Eléctrico [Wh]")
    plt.title("Energía Eléctrica")
    plt.xlabel("Índice")
    plt.ylabel("Wh")
    plt.grid(True)
    plt.legend()
    plt.show()

    print("Estado de carga final de la batería:", State_bat, "Wh")
    print("Consumo total de combustible (gal):", sum(combus), "gal")
    print("Consumo total de combustible2 (Wh):", sum(combus2), "Wh")
    print("Consumo total de E_total (Wh):", sum(E_TOTAL), "Wh")
    print("Consumo total de energía (Wh):", sum(Energy), "Wh")
    print("Consumo total de energía1 (Wh):", sum(Energy1), "Wh")
    print("Número total de rutas:", len(df))
    print("Velocidad promedio:", sum(all_speeds) / len(all_speeds), "km/h")
    print("Pendiente promedio:", sum(all_slopes) / len(all_slopes), "°")
    print("¡Proceso completado!")

    # Agregar marcadores naranjas en el mapa para los puntos de recarga
    for rp in recharges:
        folium.Marker(rp, tooltip="Recarga", icon=folium.Icon(color="orange")).add_to(m)
    m.save("rutas.html")
    print("Se guardó rutas.html")
    try:
        webbrowser.open("rutas.html")
    except:
        pass