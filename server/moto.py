import math
from geopy.distance import geodesic

class Moto:
    def __init__(self, name, route_data, stations, hybrid_cont):
        self.name = name
        self.route_data = route_data
        self.stations = stations
        self.positions = []

        # Capacidad total de batería (kWh)
        self.capacidad_bateria = 2.5
        self.estado_bateria = self.capacidad_bateria

        self.en_carga = False
        # Umbral de energía para decidir recarga
        self.umbral_energia = self.capacidad_bateria * 0.95
        self.energia_antes_de_recarga = None

        # Índices de recorrido
        self.idx = 0          # segmento (tramo)
        self.idx_ruta = 0     # índice dentro del segmento

        # Híbrido: 0 = 100% eléctrica, 1 = 100% combustión
        self.hybrid_cont = hybrid_cont

        # Consumos instantáneos por paso (kWh)
        self.pow_consumption = 0.0   # eléctrico
        self.pcn_consumption = 0.0   # combustión

        # Acumulados de energía en todo el recorrido (kWh)
        self.total_electric_kwh = 0.0
        self.total_combustion_kwh = 0.0

        # Parámetro del cargador (potencia fija, para tiempo de carga)
        self.charger_power_kw = 3.5  # por ejemplo, cargador ~3.5 kW

        # Distancia y duración total de la ruta (m, s)
        self.distance = 0.0
        self.duration = 0.0

        # Históricos
        self.puntos_recarga_realizados = []  # se llenará con dicts
        self.soc_history = []                # historial de estado de batería
        self.power = []                      # historial de potencia (kW)

        # Modelo HEV según tipo
        if hybrid_cont == 0:
            from HybridBikeConsumptionModel.parameters_electric import HEV
        else:
            from HybridBikeConsumptionModel.parameters_hybrid import HEV
        self.hev = HEV()

    def nearest_station(self, current_pos):
        destiny = self.route_data[self.idx]["coords"][-1][:2]

        distancias = [
            geodesic(current_pos[::-1], coords[::-1]).meters
            + geodesic(coords[::-1], destiny[::-1]).meters
            for coords in self.stations["coords"]
        ]

        idx_est = distancias.index(min(distancias))
        return idx_est

    def add_charge_point(self, station_idx, current_pos):
        """
        Marca el inicio de un punto de recarga.
        El valor de energy_charged se rellenará cuando realmente se haga la carga.
        """
        self.puntos_recarga_realizados.append({
            "station_name": self.stations["nombre"][station_idx],
            "station_coords": self.stations["coords"][station_idx],
            "start_coords": current_pos,
            # Se sobrescribe en self.charge()
            "energy_charged": 0.0,
        })

    def change_route(self, new_route):
        """
        Inserta una nueva ruta (por ejemplo hacia estación) en el plan actual,
        cortando el segmento actual en el punto donde se va a desviar.
        """
        self.route_data[self.idx]["coords"] = self.route_data[self.idx]["coords"][:self.idx_ruta + 1]
        self.route_data[self.idx]["speeds"] = self.route_data[self.idx]["speeds"][:self.idx_ruta + 1]
        self.route_data[self.idx]["slopes"] = self.route_data[self.idx]["slopes"][:self.idx_ruta + 1]

        self.route_data = (
            self.route_data[:self.idx + 1] +
            new_route +
            self.route_data[self.idx + 1:]
        )

        # Reiniciamos índices para seguir sobre la nueva ruta
        self.idx_ruta = 0
        self.idx += 1

    def charge(self):
        """
        Simula una recarga completa de la batería en el último punto de recarga registrado.
        Calcula cuánta energía se cargó y el tiempo estimado de carga.
        """
        # Energía que falta para llenarse (kWh)
        energy_charged = self.capacidad_bateria - self.estado_bateria

        # Batería pasa a estar llena
        self.estado_bateria = self.capacidad_bateria

        # Tiempo estimado de carga con potencia fija
        if self.charger_power_kw > 0:
            charge_time_h = energy_charged / self.charger_power_kw
        else:
            charge_time_h = 0.0

        # Guardamos detalles en el último punto de recarga
        last_cp = self.puntos_recarga_realizados[-1]
        last_cp["energy_charged"] = energy_charged           # kWh
        last_cp["charge_time_h"] = charge_time_h             # horas
        last_cp["charge_time_min"] = charge_time_h * 60.0    # minutos
        last_cp["charger_power_kw"] = self.charger_power_kw  # potencia del cargador

        # Log del SoC después de cargar
        self.soc_history.append(self.estado_bateria)
        self.en_carga = False

    def consume_step(self):
        """
        Calcula fuerzas, potencias y consumos en un "paso" de la simulación
        y actualiza la batería y los acumulados de consumo.
        """
        hev = self.hev
        segment = self.route_data[self.idx]

        if self.idx_ruta >= len(segment["coords"]):
            return False  # fin de este segmento

        vel = segment["speeds"][self.idx_ruta]
        theta = math.radians(segment["slopes"][self.idx_ruta])

        # Fuerzas
        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * math.cos(theta)
        fg = hev.Ambient.g * hev.Chassis.m * math.sin(theta)
        v_prev = segment["speeds"][self.idx_ruta - 1] if self.idx_ruta > 0 else 0
        f_inertia = hev.Chassis.m * (vel - v_prev)

        fres = faero + froll + fg + f_inertia

        # Potencias en el tren motriz
        p_m = (fres * hev.Wheel.rw) * (vel / hev.Wheel.rw)

        # Parte eléctrica
        p_eb = p_m * (1 - self.hybrid_cont) / 0.85
        factor_correccion = 1.617
        p_eb = max(0, p_eb * factor_correccion)

        # Parte combustión
        p_cn = p_m * (self.hybrid_cont) / 0.2
        factor_correccion_combustion = 1.8
        p_cn = max(0, p_cn * factor_correccion_combustion)

        # Tiempo entre este punto y el anterior
        if self.idx_ruta == 0:
            delta_t = segment["times"][0] if segment["times"][0] > 0 else 1.0
        else:
            delta_t = max(
                segment["times"][self.idx_ruta] - segment["times"][self.idx_ruta - 1],
                0.1,
            )

        # Consumos en este paso (kWh)
        tiempo_horas = delta_t / 3600.0
        self.pow_consumption = (p_eb / 1000.0) * tiempo_horas
        self.pcn_consumption = (p_cn / 1000.0) * tiempo_horas

        # Acumular consumos totales
        self.total_electric_kwh += self.pow_consumption
        self.total_combustion_kwh += self.pcn_consumption

        # Cálculo del SoC basado en consumo acumulado
        prev_soc = self.soc_history[-1] if len(self.soc_history) > 0 else self.capacidad_bateria
        prev_consumo = self.capacidad_bateria - prev_soc
        consumo_kwh = self.pow_consumption
        cons_acum = consumo_kwh + prev_consumo

        # Actualizar estado de batería
        self.estado_bateria = max(0, self.capacidad_bateria - cons_acum)
        self.soc_history.append(self.estado_bateria)

        # Guardar potencia (kW) y posición
        potencia_kw = p_eb / 1000.0
        self.power.append(potencia_kw)
        self.positions.append(segment["coords"][self.idx_ruta])

        return True

    def avanzar_paso(self):
        """
        Avanza un paso de simulación. Devuelve:
        0 -> fin de la ruta
        1 -> continuar
        3 -> batería baja, hay que recargar/rutear a estación
        """
        # 1) Consumir energía en este paso
        if not self.consume_step():
            # Fin del segmento actual
            self.duration += self.route_data[self.idx]["duration"]
            self.distance += self.route_data[self.idx]["distance"]

            self.idx += 1
            self.idx_ruta = 0

            # ¿se acabaron todos los segmentos?
            if self.idx >= len(self.route_data):
                return 0

            # Si estaba en carga al final del segmento, completar la carga
            if self.en_carga:
                self.charge()

            return 1

        # 2) Revisar batería
        if self.estado_bateria < self.umbral_energia and not self.en_carga:
            self.en_carga = True
            return 3  # señal: batería baja, toca recargar

        # 3) Avanzar al siguiente índice dentro del segmento
        self.idx_ruta += 1
        return 1