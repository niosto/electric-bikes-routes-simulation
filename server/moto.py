import math
from geopy.distance import geodesic

class Moto:
    def __init__(self, name, route_data, stations, hybrid_cont):
        self.name = name
        self.route_data = route_data
        self.stations = stations
        self.positions = []
        self.capacidad_bateria = 2.5
        self.estado_bateria = self.capacidad_bateria
        self.en_carga = False
        self.umbral_energia = self.capacidad_bateria * 0.9
        self.energia_antes_de_recarga = None
        self.idx = 0
        self.idx_ruta = 0
        self.hybrid_cont = hybrid_cont

        self.pow_consumption = 0
        self.pcn_consumption = 0
        
        self.distance = 0.0
        self.duration = 0.0

        self.puntos_recarga_realizados = []
        self.soc_history = []
        self.power = []

        if hybrid_cont == 0:
            from HybridBikeConsumptionModel.parameters_electric import HEV
        else:
            from HybridBikeConsumptionModel.parameters_hybrid import HEV
        self.hev = HEV()

    def nearest_station(self, current_pos):
        distancias = [geodesic(current_pos[:2], coords).meters for coords in self.stations["coords"]]
        idx_est = distancias.index(min(distancias))
        return idx_est

    def add_charge_point(self, station_idx, current_pos):
        self.puntos_recarga_realizados.append({
            "station_name": self.stations["nombre"][station_idx],
            "station_coords": self.stations["coords"][station_idx],
            "start_coords": current_pos,
            "energy_charged": self.estado_bateria,
        })

    def change_route(self, new_route):
        self.route_data[self.idx]["coords"] = self.route_data[self.idx]["coords"][:self.idx_ruta + 1]
        self.route_data[self.idx]["speeds"] = self.route_data[self.idx]["speeds"][:self.idx_ruta + 1]
        self.route_data[self.idx]["slopes"] = self.route_data[self.idx]["slopes"][:self.idx_ruta + 1]

        self.route_data = self.route_data[:self.idx + 1] + new_route + self.route_data[self.idx + 1:] 

        self.idx_ruta += 1

    def charge(self):
        energy_charged = self.capacidad_bateria - self.estado_bateria
        self.estado_bateria = self.capacidad_bateria
        self.puntos_recarga_realizados[-1]["energy_charged"] = energy_charged
        self.en_carga = False

    def consume_step(self):
        hev = self.hev

        segment = self.route_data[self.idx]

        if self.idx_ruta >= len(segment["coords"]):
            return False  # reached end of this segment

        vel = segment["speeds"][self.idx_ruta] 
        theta = math.radians(segment["slopes"][self.idx_ruta])

        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        
        froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * math.cos(theta)
        fg = hev.Ambient.g * hev.Chassis.m * math.sin(theta)
        v_prev = segment["speeds"][self.idx_ruta - 1] if self.idx_ruta > 0 else 0
        f_inertia = hev.Chassis.m * (vel - v_prev)

        fres = faero + froll + fg + f_inertia
        p_m = (fres * hev.Wheel.rw) * (vel / hev.Wheel.rw)
        p_eb = p_m * (1 - self.hybrid_cont) / 0.85
        # Factor de corrección empírico (1.617) para ajustar a datos reales de telemetría
        # Justificación: El modelo simplificado solo considera eficiencia del tren motriz (85%),
        # pero no incluye pérdidas adicionales del sistema completo:
        # - Pérdidas en cadena de conversión eléctrica (inversor, controlador, BMS): ~15-20%
        # - Pérdidas por calentamiento (resistencia interna, cables, histéresis): ~5-10%
        # - Pérdidas mecánicas adicionales (rodamientos, transmisión, frenos): ~5-9%
        # - Consumo de sistemas auxiliares (electrónica, ventilación): ~2-5%
        # Relación matemática: Pérdidas adicionales = (Factor - 1) / Factor
        # Pérdidas adicionales = (1.617 - 1) / 1.617 = 38.14%
        # Eficiencia real del sistema = 85% / 1.617 = 52.58%
        # Validación: Calculado a partir de 1708 puntos de telemetría real
        # (Potencia real: 268.68 kW / Potencia modelo: 166.21 kW = 1.617)
        factor_correccion = 1.617
        p_eb = max(0,p_eb * factor_correccion)
        p_cn = p_m * (self.hybrid_cont) / 0.2
        factor_correccion_combustion = 1.8
        p_cn = max(0, p_cn * factor_correccion_combustion)
        
        consumo_wh = p_eb / 3600.0

        if self.idx_ruta == 0:
            delta_t = segment["times"][0] if segment["times"][0] > 0 else 1.0
        else:
            delta_t = max(segment["times"][self.idx_ruta] - segment["times"][self.idx_ruta - 1], 0.1)
        
        prev_soc = self.soc_history[-1] if len(self.soc_history) > 0 else self.capacidad_bateria
        
        tiempo_horas = delta_t / 3600
        self.pow_consumption = (p_eb / 1000) * tiempo_horas
        self.pcn_consumption = (p_cn / 1000) * tiempo_horas
        
        consumo_kwh = (p_eb / 1000) * tiempo_horas
        
        prev_consumo = self.capacidad_bateria - prev_soc

        cons_acum = consumo_kwh + prev_consumo
        potencia_kw = p_eb / 1000

        # update state
        self.estado_bateria = max(0, self.capacidad_bateria - cons_acum)    
        self.soc_history.append(self.estado_bateria)
        self.power.append(potencia_kw)
        self.positions.append(segment["coords"][self.idx_ruta])

        return True

    def avanzar_paso(self):
        # 1) Consume energy for this step
        if not self.consume_step():
            # reached end of current segment
            self.duration += self.route_data[self.idx]["duration"]
            self.distance += self.route_data[self.idx]["distance"]

            self.idx += 1
            self.idx_ruta = 0

            # all segments done
            if self.idx >= len(self.route_data):
                return 0

            # check charging after segment ends
            if self.en_carga:
                self.charge()

            return 1

        # 2) Check battery
        if self.estado_bateria < self.umbral_energia and not self.en_carga:
            self.en_carga = True
            return 3  # signal: low battery

        # 3) advance step
        self.idx_ruta += 1
        return 1  # continue