import math
from geopy.distance import geodesic
from HybridBikeConsumptionModel.parameters_electric import HEV

class Moto:
    def __init__(self, name, route_data, stations):
        self.name = name
        self.route_data = route_data
        self.stations = stations
        self.positions = []

        # Capacidad de la batería (kWh, por ejemplo 2.5)
        self.capacidad_bateria = 2.5
        # Estado actual de la batería (mismo tipo de unidad que capacidad)
        self.estado_bateria = self.capacidad_bateria

        # Flags de carga
        self.en_carga = False
        self.umbral_energia = self.capacidad_bateria * 0.1  # 10% de la capacidad
        self.energia_antes_de_recarga = None

        # Índices de recorrido
        self.idx = 0          # índice de segmento
        self.idx_route = 0    # índice dentro del segmento (punto)

        # Acumuladores de distancia y duración (para resumen)
        self.distance = 0.0
        self.duration = 0.0

        # Historiales y registros
        self.puntos_recarga_realizados = []
        self.soc_history = []
        self.power = []

    # -------------------------------------------------------
    def nearest_station(self, current_pos):
        destiny = self.route_data[self.idx]["coords"][-1][:2]

        distancias = [
            geodesic(current_pos[::-1], coords[::-1]).meters
            + geodesic(coords[::-1], destiny[::-1]).meters
            for coords in self.stations["coords"]
        ]

        idx_est = distancias.index(min(distancias))
        return idx_est

    # -------------------------------------------------------
    def add_charge_point(self, station_idx, current_pos):
        """
        Registra que vamos a hacer una recarga en cierta estación.
        Dejamos energy_charged en 0, y se actualiza al finalizar la recarga en charge().
        """
        # Guardamos el estado de batería antes de iniciar la recarga
        self.energia_antes_de_recarga = self.estado_bateria

        self.puntos_recarga_realizados.append(
            {
                "station_name": self.stations["nombre"][station_idx],
                "station_coords": self.stations["coords"][station_idx],
                "start_coords": current_pos,
                "energy_charged": 0.0,  # se actualizará cuando termine de cargar
            }
        )

    # -------------------------------------------------------
    def change_route(self, new_route):
        """
        Cambia la ruta actual para dirigir la moto hacia una estación de recarga,
        recortando el segmento actual hasta el punto donde vamos y luego insertando
        los nuevos segmentos.
        """
        # Recorta los arrays del segmento actual hasta el punto idx_route
        self.route_data[self.idx]["coords"] = self.route_data[self.idx]["coords"][
            : self.idx_route + 1
        ]
        self.route_data[self.idx]["speeds"] = self.route_data[self.idx]["speeds"][
            : self.idx_route + 1
        ]
        self.route_data[self.idx]["slopes"] = self.route_data[self.idx]["slopes"][
            : self.idx_route + 1
        ]

        # Inserta la nueva ruta después del segmento actual
        self.route_data = (
            self.route_data[: self.idx + 1]
            + new_route
            + self.route_data[self.idx + 1 :]
        )

        # Nos posicionamos en el primer punto del nuevo tramo insertado
        self.idx_route = 0

    # -------------------------------------------------------
    def charge(self):
        """
        Lógica de recarga:
        - Calcula la energía cargada como la diferencia entre la capacidad total
          y el estado actual.
        - Lleva la batería al 100%.
        - Actualiza el registro de puntos de recarga.
        """
        # Energía que se ha cargado en este punto (en la misma unidad que capacidad_bateria)
        energy_charged = max(0.0, self.capacidad_bateria - self.estado_bateria)

        # Llevamos la batería al máximo
        self.estado_bateria = self.capacidad_bateria

        # Actualizamos el último punto de recarga registrado
        if self.puntos_recarga_realizados:
            self.puntos_recarga_realizados[-1]["energy_charged"] = energy_charged

        # Guardamos el nuevo estado de batería en el historial
        self.soc_history.append(self.estado_bateria)

        # Ya no estamos en modo carga
        self.en_carga = False

    # -------------------------------------------------------
    def consume_step(self):
        hev = HEV()

        segment = self.route_data[self.idx]
        if self.idx_route >= len(segment["coords"]):
            # Ya no hay más puntos en este segmento
            return False

        vel = segment["speeds"][self.idx_route]
        theta = math.radians(segment["slopes"][self.idx_route])

        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel**2)
        froll = (
            hev.Ambient.g
            * hev.Chassis.m
            * hev.Chassis.crr
            * math.cos(theta)
        )
        fg = hev.Ambient.g * hev.Chassis.m * math.sin(theta)
        v_prev = segment["speeds"][self.idx_route - 1] if self.idx_route > 0 else 0
        f_inertia = hev.Chassis.m * (vel - v_prev)

        fres = faero + froll + fg + f_inertia
        p_m = fres * vel
        eficiencia_tren = 0.7
        p_eb = max(0, p_m / (2.8 * eficiencia_tren))
        consumo_wh = p_eb / 3600.0

        # Actualizamos estado de la batería
        self.estado_bateria = max(0, self.estado_bateria - consumo_wh)

        # Guardamos en historiales
        self.soc_history.append(self.estado_bateria)
        self.power.append(p_eb)
        self.positions.append(segment["coords"][self.idx_route])

        print(self.estado_bateria)
        return True

    # -------------------------------------------------------
    def avanzar_paso(self):
        """
        Avanza un paso en la simulación:
        - Si no hay más puntos en el segmento actual, pasa al siguiente.
        - Si la batería baja del umbral y no está en carga, activa modo carga.
        - Devuelve:
            0 -> terminó toda la ruta
            1 -> sigue avanzando normalmente
            3 -> batería baja, se requiere recarga
        """
        # 1) Consumir energía en este paso
        if not self.consume_step():
            # Llegamos al final del segmento actual
            self.duration += self.route_data[self.idx]["duration"]
            self.distance += self.route_data[self.idx]["distance"]

            self.idx += 1
            self.idx_route = 0

            # Si no hay más segmentos, fin de ruta
            if self.idx >= len(self.route_data):
                return 0

            # Si estamos en modo carga y terminó un segmento, ejecutamos la recarga
            if self.en_carga:
                self.charge()

            return 1

        # 2) Comprobar estado de batería
        if self.estado_bateria < self.umbral_energia and not self.en_carga:
            self.en_carga = True
            return 3  # señal: batería baja, se requiere recarga

        # 3) Avanzar al siguiente punto del segmento
        self.idx_route += 1
        return 1