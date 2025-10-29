
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

# Definir estaciones de recarga (coordenadas y nombre)
df = pd.read_json("data/amva_routes.json")

sdf = df[df["municipio_o"].str.contains("estacion")].groupby("municipio_o").first()[["o_long","o_lat"]].reset_index()

# Definir estaciones de recarga según los datos que tenemos(coordenadas y nombre)
estaciones = [
    ((row.o_lat, row.o_long), row.municipio_o.title())
    for _, row in sdf.iterrows()
]

# Lectura del archivo .pkl que contiene rutas (velocidades y pendientes)
ruta_archivo = "data/telemetry.json"
df_resultado = pd.read_json(ruta_archivo)
print(f"Rutas válidas encontradas: {len(df_resultado)}")

# --- Distribución de rutas entre motos para aumentar la distancia recorrida ---
# Parámetro para definir el número de motos a simular
n_motos = 1  # Modifica este valor para agregar más motos

# Se crea un diccionario donde cada moto acumulará segmentos (concatenando listas)
moto_routes = { f"moto_{i+1}": {"speeds": [], "slopes": [], "positions": []} for i in range(n_motos) }

# Distribución round-robin de todas las rutas válidas entre las motos
for idx, (_, row) in enumerate(df_resultado.iterrows()):
    n_points = len(row["speeds"])
    # Generar posiciones interpoladas entre origen y destino para el segmento
    moto_key = f"moto_{(idx % n_motos) + 1}"
    moto_routes[moto_key]["speeds"].extend(row["speeds"])
    moto_routes[moto_key]["slopes"].extend(row["slopes"])
    moto_routes[moto_key]["positions"].extend(row["coords"])

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
