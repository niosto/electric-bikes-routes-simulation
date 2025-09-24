# uv venv -p 3.11
# pip install -U uv
# uv sync --all-groups
# python agentBasedModel.py

import math
import pandas as pd
from geopy.distance import geodesic
from HybridBikeConsumptionModel.parameters_electric import HEV
import numpy as np
import webbrowser
import folium
import networkx as nx
import matplotlib.pyplot as plt

def interpolate_position(origin, destination, t):
    # Función para interpolar entre la posición origen y destino según el factor t (0 a 1)
    lat = origin[0] + t * (destination[0] - origin[0])
    lon = origin[1] + t * (destination[1] - origin[1])
    return (lat, lon)

# Parámetro para seleccionar la cantidad de rutas a usar
NUM_RUTAS = 120 # Ajusta este valor según lo que necesites

class Moto:
    def __init__(self, nombre, speeds, slopes, positions=None):
        self.nombre = nombre
        self.speeds = speeds         # Inicialización del atributo speeds
        self.slopes = slopes         # Inicialización del atributo slopes
        self.positions = positions or []
        self.estado_batería = 700.0
        self.en_recarga = False
        self.tiempo_recarga = 0
        self.umbral_energia = 0.2 * self.estado_batería
        self.tiempo_recarga_total = 60
        self.puntos_recarga_realizados = []  # Se almacenará como (coordenada, nombre_estación, paso, energía_recargada)
        self.histórico_SOC = []
        self.idx = 0
        self.distancia_total = 0.0
        # Nuevo atributo para almacenar el SOC al iniciar la recarga
        self.energy_before_recarga = None

    def avanzar_paso(self, estaciones):
        """Simula un paso de la moto en la ruta.
           Se asume que cada paso dura 1 segundo para estimar la distancia vía la velocidad.
        """
        if self.idx >= len(self.speeds):
            return False

        # 1) Si la moto está en recarga, aumentar contador y, al finalizar, calcular energía recargada
        if self.en_recarga:
            self.tiempo_recarga += 1
            if self.tiempo_recarga >= self.tiempo_recarga_total:
                # Calcular la energía recargada en este proceso
                energy_recargada = 700.0 - self.energy_before_recarga
                # Reemplazar el None por la energía recargada
                coord, nombre_est, paso, _ = self.puntos_recarga_realizados[-1]
                self.puntos_recarga_realizados[-1] = (coord, nombre_est, paso, energy_recargada)
                self.en_recarga = False
                self.tiempo_recarga = 0
                self.estado_batería = 700.0  # Batería recargada al 100%
                self.energy_before_recarga = None
            return True

        # 2) Si la batería es baja, buscar la estación de recarga más cercana
        if self.estado_batería < self.umbral_energia:
            current_pos = None
            if self.positions and self.idx < len(self.positions):
                current_pos = self.positions[self.idx]
            if current_pos:
                distancias = [geodesic(current_pos, est[0]).meters for est in estaciones]
                idx_est = distancias.index(min(distancias))
            else:
                idx_est = 0
            print(self.positions)
            coord_est, nombre_est = estaciones[idx_est]
            self.en_recarga = True
            # Guardar el SOC actual para calcular la energía recargada
            self.energy_before_recarga = self.estado_batería
            # Registrar el evento de recarga con un placeholder para energía
            self.puntos_recarga_realizados.append((coord_est, nombre_est, self.idx, None))
            return True

        # 3) Avanzar un paso y calcular consumo
        vel = self.speeds[self.idx] / 3.6  # Conversión de km/h a m/s
        theta = math.radians(self.slopes[self.idx])
        hev = HEV()

        # Fuerzas y potencia (tomados de ModeloMoto1)
        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * math.cos(theta)
        fg    = hev.Ambient.g * hev.Chassis.m * math.sin(theta)
        if self.idx == 0:
            delta_v = vel
        else:
            v_prev = self.speeds[self.idx - 1] / 3.6
            delta_v = vel - v_prev
        f_inertia = hev.Chassis.m * (delta_v / 1.0)
        fres = faero + froll + fg + f_inertia
        p_m = fres * vel
        eficiencia_tren = 0.7
        p_eb = p_m / eficiencia_tren
        consumo_wh = p_eb / 3600.0

        self.estado_batería -= consumo_wh
        if self.estado_batería < 0:
            self.estado_batería = 0.0
        self.histórico_SOC.append(self.estado_batería)

        self.distancia_total += vel / 1000.0

        self.idx += 1
        return True

# Scheduler simple sin mesa.time
class SimpleScheduler:
    def __init__(self, model):
        self.model = model
        self.agents = []
    def add(self, agent):
        self.agents.append(agent)
    def step(self):
        for agent in self.agents:
            agent.step()

# Agente Mesa que envuelve a una instancia de Moto
from mesa import Agent, Model
class MotoAgent(Agent):
    def __init__(self, unique_id, model, moto):
        # Inicialización manual para evitar conflictos con super().__init__()
        self.unique_id = unique_id
        self.model = model
        self.moto = moto
    def step(self):
        self.moto.avanzar_paso(self.model.estaciones)

# Modelo Mesa que utiliza el scheduler simple
class MotoModel(Model):
    def __init__(self, moto_list, estaciones):
        super().__init__()
        self.estaciones = estaciones
        self.schedule = SimpleScheduler(self)
        for i, moto in enumerate(moto_list):
            agent = MotoAgent(i, self, moto)
            self.schedule.add(agent)
    def step(self):
        self.schedule.step()

if __name__ == "__main__":
    # Definir estaciones de recarga (coordenadas y nombre)
    estaciones = [
        ((6.197639, -75.5781), "Estación EAFIT"),
        ((6.197860, -75.5597), "Estación El Tesoro"),
        ((6.186745, -75.5620), "Estación Los Balsos")
    ]

    # Lectura del archivo .pkl que contiene rutas (velocidades y pendientes)
    ruta_archivo = "speed_slope_smooth.pkl"
    data = pd.read_pickle(ruta_archivo)

    # Creación de registros filtrando rutas con listas válidas de velocidades y pendientes
    registros = []
    for origen, row in data.iterrows():
        for destino, valores in row.items():
            if (isinstance(valores, dict) and 
                'speeds' in valores and 
                'slopes' in valores and 
                len(valores['speeds']) > 0):
                registros.append({
                    'from_lat_lon': origen,
                    'to_lat_lon': destino,
                    'speeds': valores['speeds'],
                    'slopes': valores['slopes']
                })
    df_resultado = pd.DataFrame(registros)
    print(f"Rutas válidas encontradas: {len(df_resultado)}")

    # Escoger solo la cantidad deseada de rutas
    df_resultado = df_resultado.head(NUM_RUTAS)
    print(f"Usando solo las primeras {NUM_RUTAS} rutas.")

    # --- Distribución de rutas entre motos para aumentar la distancia recorrida ---
    # Parámetro para definir el número de motos a simular
    n_motos = 5  # Modifica este valor para agregar más motos

    # Se crea un diccionario donde cada moto acumulará segmentos (concatenando listas)
    moto_routes = { f"moto_{i+1}": {"speeds": [], "slopes": [], "positions": []} for i in range(n_motos) }

    # Distribución round-robin de todas las rutas válidas entre las motos
    for idx, (_, row) in enumerate(df_resultado.iterrows()):
        n_points = len(row["speeds"])
        # Generar posiciones interpoladas entre origen y destino para el segmento
        positions = [interpolate_position(row["from_lat_lon"], row["to_lat_lon"],
                                          (j/(n_points-1)) if n_points > 1 else 0)
                     for j in range(n_points)]
        moto_key = f"moto_{(idx % n_motos) + 1}"
        moto_routes[moto_key]["speeds"].extend(row["speeds"])
        moto_routes[moto_key]["slopes"].extend(row["slopes"])
        moto_routes[moto_key]["positions"].extend(positions)

    # Crear instancias de Moto (agentes) para cada moto
    flotilla = []
    for nombre, datos in moto_routes.items():
        m = Moto(
            nombre=nombre,
            speeds=datos["speeds"],
            slopes=datos["slopes"],
            positions=datos.get("positions", None)
        )
        flotilla.append(m)
    
    # Bucle principal de simulación (mientras alguna moto pueda avanzar)
    activo = True
    paso = 0
    while activo:
        activo = False
        for moto in flotilla:
            if moto.avanzar_paso(estaciones):
                activo = True
        paso += 1

    # Mostrar resultados de la simulación para cada moto
    for moto in flotilla:
        print("-"*40)
        print(f"Resultados para: {moto.nombre}")
        if moto.puntos_recarga_realizados:
            print("Puntos de recarga realizados:")
            for recarga in moto.puntos_recarga_realizados:
                if len(recarga) == 3:
                    coord, nombre_est, paso_recarga = recarga
                    print(f"  • {nombre_est} en {coord} en el paso {paso_recarga} (recarga en curso o sin dato de energía)")
                elif len(recarga) == 4:
                    coord, nombre_est, paso_recarga, energia_recargada = recarga
                    print(f"  • {nombre_est} en {coord} en el paso {paso_recarga} - Energía recargada: {energia_recargada:.2f} Wh")
            print(f"Recargas totales: {len(moto.puntos_recarga_realizados)}")
        else:
            print("No realizó recargas en la simulación.")
        print(f"Último SOC registrado: {moto.histórico_SOC[-1]:.2f} Wh" if moto.histórico_SOC else "Último SOC registrado: N/A Wh")
        print(f"Pasos totales recorridos: {moto.idx}")
        if moto.speeds:
            velocidad_promedio = sum(moto.speeds) / len(moto.speeds)
        else:
            velocidad_promedio = 0
        print(f"Velocidad promedio (ruta original): {velocidad_promedio:.2f} km/h")
        print(f"Distancia total recorrida: {moto.distancia_total:.3f} km\n")

    # Mostrar rutas y puntos de recarga en un solo mapa con Folium
    center_map = df_resultado.iloc[0]["from_lat_lon"]
    m_map = folium.Map(location=center_map, zoom_start=14)
    # Dibujar rutas
    for idx, row in df_resultado.iterrows():
        from_coords = row["from_lat_lon"]
        to_coords = row["to_lat_lon"]
        folium.Marker(from_coords, tooltip=f"Origen {idx}", icon=folium.Icon(color="green")).add_to(m_map)
        folium.Marker(to_coords, tooltip=f"Destino {idx}", icon=folium.Icon(color="red")).add_to(m_map)
        folium.PolyLine([from_coords, to_coords], color="blue", weight=4).add_to(m_map)
    # Agregar marcadores de recarga (naranja)
    for moto in flotilla:
        for rp in moto.puntos_recarga_realizados:
            folium.Marker(rp[0], tooltip="Recarga", icon=folium.Icon(color="orange")).add_to(m_map)
    m_map.save("rutas.html")
    print("Se guardó rutas.html")
    try:
        webbrowser.open("rutas.html")
    except:
        pass

    # Graficar la evolución del SOC usando Matplotlib
    colors = ["red", "blue", "green", "orange", "purple", "brown", "pink", "gray"]
    plt.figure(figsize=(10, 6))
    for i, moto in enumerate(flotilla):
        color = colors[i % len(colors)]
        pasos = range(len(moto.histórico_SOC))
        plt.plot(pasos, moto.histórico_SOC, label=moto.nombre, color=color)
    plt.title("Evolución del SOC de las motos")
    plt.xlabel("Paso de simulación")
    plt.ylabel("Estado de carga (Wh)")
    plt.legend()
    plt.grid(True)
    plt.show()

    # ===================== CÁLCULO DE REDUCCIÓN NETA DE EMISIONES =====================
    # Factores de emisión (ajusta según tu país o fuente)
    FACTOR_EMISION_COMBUSTION = 0.12  # kg CO2 por km (ejemplo para moto a gasolina)
    FACTOR_EMISION_ELECTRICA = 0.0004  # kg CO2 por Wh consumido (ejemplo, depende de la matriz eléctrica)

    emisiones_combustion = []  # Lista para almacenar emisiones por combustión por moto
    emisiones_electricas = []  # Lista para almacenar emisiones eléctricas por moto

    for moto in flotilla:
        # Emisiones si fuera combustión (solo depende de la distancia recorrida)
        emi_comb = moto.distancia_total * FACTOR_EMISION_COMBUSTION
        emisiones_combustion.append(emi_comb)
        # Emisiones reales eléctricas (depende del consumo total)
        consumo_total_wh = 700.0 - moto.histórico_SOC[-1] if moto.histórico_SOC else 0
        emi_elec = consumo_total_wh * FACTOR_EMISION_ELECTRICA
        emisiones_electricas.append(emi_elec)

    total_combustion = sum(emisiones_combustion)
    total_electricas = sum(emisiones_electricas)
    N_motos = len(flotilla)

    reduccion_neta = (total_combustion - total_electricas)
    print("\n================= RESUMEN DE EMISIONES =================")
    print(f"Reducción neta de emisiones para {N_motos} motos eléctricas: {reduccion_neta:.2f} kg CO2")
    print(f"Emisiones totales si fueran a combustión: {total_combustion:.2f} kg CO2")
    print(f"Emisiones totales reales eléctricas: {total_electricas:.2f} kg CO2")
    print("\nDetalle por moto:")
    for i, moto in enumerate(flotilla):
        print(f"{moto.nombre}: Emisiones combustión = {emisiones_combustion[i]:.2f} kg CO2, Emisiones eléctricas = {emisiones_electricas[i]:.2f} kg CO2")