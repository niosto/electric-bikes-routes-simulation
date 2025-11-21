import math
from geopy.distance import geodesic
from HybridBikeConsumptionModel.parameters_electric import HEV

class Moto:
    def __init__(self, name, route_data, stations):
        self.name = name
        self.route_data = route_data
        self.stations = stations
        self.positions = []
        self.capacidad_bateria = 2.5
        self.estado_bateria = self.capacidad_bateria
        self.en_carga = False
        self.umbral_energia = self.capacidad_bateria * 0.1
        self.energia_antes_de_recarga = None
        self.idx = 0
        self.idx_route = 0
        
        self.distance = 0.0
        self.duration = 0.0

        self.puntos_recarga_realizados = []
        self.soc_history = []
        self.power = []

    def nearest_station(self, current_pos):
        destiny = self.route_data[self.idx]["coords"][-1][:2]

        distancias = [geodesic(current_pos[::-1], coords[::-1]).meters
              + geodesic(coords[::-1], destiny[::-1]).meters
               for coords in self.stations["coords"]]
        
        # COndicional para saber si la distancia es 
        #din = min(distancias)
        #if self.estado_bateria   
        # Unidad de la bateria kiloVatios
         
        idx_est = distancias.index(min(distancias))
        return idx_est

    def add_charge_point(self, station_idx, current_pos):
        self.puntos_recarga_realizados.append({
            "station_name": self.stations["nombre"][station_idx],
            "station_coords": self.stations["coords"][station_idx],
            "start_coords": current_pos,
            "energy_charged": self.battery_state,
        })

    def change_route(self, new_route):
        self.route_data[self.idx]["coords"] = self.route_data[self.idx]["coords"][:self.idx_ruta + 1]
        self.route_data[self.idx]["speeds"] = self.route_data[self.idx]["speeds"][:self.idx_ruta + 1]
        self.route_data[self.idx]["slopes"] = self.route_data[self.idx]["slopes"][:self.idx_ruta + 1]

        self.route_data = self.route_data[:self.idx + 1] + new_route + self.route_data[self.idx + 1:] 

        self.idx_route += 1

    def charge(self):
        self.puntos_recarga_realizados[-1]["energy_charged"] = energy_charged
        self.soc_history.append(self.estado_bateria)
        self.en_carga = False

    def consume_step(self):
        hev = HEV()

        segment = self.route_data[self.idx]
        if self.idx_route >= len(segment["coords"]):
            return False  # reached end of this segment

        vel = segment["speeds"][self.idx_route] 
        theta = math.radians(segment["slopes"][self.idx_route])

        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * math.cos(theta)
        fg = hev.Ambient.g * hev.Chassis.m * math.sin(theta)
        v_prev = segment["speeds"][self.idx_route - 1] if self.idx_route > 0 else 0
        f_inertia = hev.Chassis.m * (vel - v_prev)

        fres = faero + froll + fg + f_inertia
        p_m = fres * vel
        eficiencia_tren = 0.7
        p_eb = max(0, p_m / (2.8 * eficiencia_tren))
        consumo_wh = p_eb / 3600.0

        # update state
        self.battery_state = max(0, self.battery_state - consumo_wh)
        self.soc_history.append(self.battery_state)
        self.power.append(p_eb)
        self.positions.append(segment["coords"][self.idx_route])

        print(self.battery_state)
        return True

    # -------------------------------------------------------
    def avanzar_paso(self):
        # 1) Consume energy for this step
        if not self.consume_step():
            # reached end of current segment
            self.duration += self.route_data[self.idx]["duration"]
            self.distance += self.route_data[self.idx]["distance"]

            self.idx += 1
            self.idx_route = 0

            # all segments done
            if self.idx >= len(self.route_data):
                return 0

            # check charging after segment ends
            if self.in_charge:
                self.charge()

            return 1

        # 2) Check battery
        if self.battery_state < self.umbral_energia and not self.in_charge:
            self.in_charge = True
            return 3  # signal: low battery

        # 3) advance step
        self.idx_route += 1
        return 1  # continue