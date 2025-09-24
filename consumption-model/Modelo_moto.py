
#import pickle
#import pandas as pd
#import webbrowser
#from geopy.distance import geodesic
#import folium
#import networkx as nx
#import matplotlib.pyplot as plt

def bike_model_particle(hybrid_cont, speeds, slopes):
    import numpy as np
    import math
    if hybrid_cont == 0:
        from HybridBikeConsumptionModel.parameters_electric import HEV
    else:
        from HybridBikeConsumptionModel.parameters_hybrid import HEV
    hev = HEV()
    last_vel = 0
    p = []
    State_bater = 3700
    Energy = []
    Energy1 = []
    combus= []
    combus2 =[]
    E_TOTAL = []

    for i in range(len(speeds)):
        vel = speeds[i]
        #vel = speeds[i]/3.6
        theta = slopes[i]*math.pi/180
        faero = 0.5 * hev.Ambient.rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        # Rolling force
        froll = hev.Ambient.g * hev.Chassis.m * hev.Chassis.crr * np.cos(theta)
        fg = hev.Ambient.g * hev.Chassis.m * np.sin(theta)
        delta_v = vel - last_vel
        #print(vel,last_vel)
        f_inertia = hev.Chassis.m * delta_v / 1
        # Sum Forces
        fres = faero + froll + fg + f_inertia
        p_e = vel * fres
        p_m = (fres * hev.Wheel.rw) * (vel / hev.Wheel.rw)
        p_eb = p_m * (1 - hybrid_cont) / 0.7
        p_cn = p_m * (hybrid_cont) / 0.2

        if p_cn <= 0:
            p_cn = 0

        last_vel = vel
        pow_consumption = p_eb/3600  # watts hour
        pcn_consumption = p_cn/3600  # watts hour
        result = pow_consumption
        result1 = State_bater - pow_consumption  #self.State_bater - 
        result2 = pcn_consumption / 36718.50158230244 #galones
        result3 = pcn_consumption 
        Energy.append(result1) #Energía estado de carga batería
        Energy1.append(result) #Consumo en vatios hora
        combus.append(result2) #Consumo gasolina - galones
        combus2.append(result3) #Consumo energético en hibrido (Motor combustión-equivalente)
        E_TOTAL.append(pow_consumption + pcn_consumption) #Potenicia Total
        State_bater = result1
        if State_bater > 3700:
           State_bater = 3700

    return   State_bater, combus, combus2, E_TOTAL, Energy, Energy1