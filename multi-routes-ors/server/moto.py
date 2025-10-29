from HybridBikeConsumptionModel.parameters_electric import HEV

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
        self.potencia = []
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

        # eta_motor = 0.9
        # eta_buck = 0.96
        # eta_batt = 0.93
        # eta_chain = 0.95

        # ef_total = eficiencia_tren * eta_motor * eta_buck * eta_batt * eta_chain
        # p_eb = p_m / ef_total

        p_eb = p_m / (2.8*eficiencia_tren)
        
        consumo_wh = p_eb / 3600.0

        if p_eb < 0:
            p_eb = 0
            
        self.potencia.append(p_eb)


        self.estado_batería -= consumo_wh
        if self.estado_batería < 0:
            self.estado_batería = 0.0
        self.histórico_SOC.append(self.estado_batería)

        self.distancia_total += vel / 1000.0

        self.idx += 1
        return True
