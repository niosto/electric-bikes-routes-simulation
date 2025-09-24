# --- Función modificada para simular un segmento de ruta con acumulación de batería ---
def bike_model_segment(hybrid_cont, speeds, slopes, init_bat=3700):
    """
    Simula un segmento de ruta usando las listas de velocidades y pendientes.
    Recibe el estado de batería inicial y retorna el estado final junto con la lista
    de consumo de energía (Wh) en cada paso.
    """
    import numpy as np
    import math
    if hybrid_cont == 0:
        from HybridBikeConsumptionModel.parameters_electric import HEV
    else:
        from HybridBikeConsumptionModel.parameters_hybrid import HEV
    hev = HEV()
    last_vel = 0
    E_TOTAL = []  # consumo en cada paso (Wh)
    State_bater = init_bat
    for i in range(len(speeds)):
        vel = speeds[i] / 3.6  # convertir km/h a m/s
        theta = slopes[i] * math.pi / 180  # convertir grados a radianes
        # Cálculo de fuerzas:
        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * math.cos(theta)
        fg = hev.Ambient.g * hev.Chassis.m * math.sin(theta)
        delta_v = vel - last_vel
        f_inertia = hev.Chassis.m * delta_v  # supondremos intervalo de 1 s
        fres = faero + froll + fg + f_inertia
        p_e = vel * fres
        p_m = (fres * hev.Wheel.rw) * (vel / hev.Wheel.rw)
        p_eb = p_m * (1 - hybrid_cont) / 0.7
        p_cn = p_m * (hybrid_cont) / 0.2
        if p_cn <= 0:
            p_cn = 0
        last_vel = vel
        pow_consumption = p_eb / 3600  # Wh
        pcn_consumption = p_cn / 3600  # Wh
        consumption = pow_consumption + pcn_consumption
        E_TOTAL.append(consumption)
        # Actualizamos el estado de la batería con la parte eléctrica consumida
        State_bater = State_bater - pow_consumption  
    return State_bater, E_TOTAL