# Modelo de Simulación (Eléctrico/Híbrido) y Basado en Agentes

Este proyecto implementa diferentes modelos para simular el consumo de energía (eléctrica y/o combustible) de un vehículo (motocicleta) bajo perfiles de velocidad y pendiente variables. Se abordan tres niveles de modelado: un modelo dinámico continuo detallado, un modelo de partícula discreto simplificado y una simulación basada en agentes para explorar el comportamiento de una flota y la interacción con la infraestructura de recarga.

## Estructura del Proyecto

El código se organiza en los siguientes archivos:
── model.py
├── functions.py
├── ModeloMoto1.py
├── agentBasedModel.py
├── speed_slope_smooth.pkl # Archivo de datos de perfiles de velocidad y pendiente (asumido existente)
└── HybridBikeConsumptionModel/
├── init.py 
├── parameters_electric.py
└── parameters_hybrid.py


## Descripción de los Archivos

*   **`HybridBikeConsumptionModel/parameters_electric.py`**:
    Define la clase `HEV` que contiene todos los **parámetros físicos y eléctricos fijos** para un **modelo de vehículo puramente eléctrico**. Incluye propiedades del chasis (masa, arrastre aerodinámico, rodadura), radio de rueda, parámetros de la batería (voltaje de circuito abierto OCV, resistencias internas R0/R1, capacitancia C1, capacidad total q, eficiencia de Coulomb n) y parámetros del motor eléctrico y convertidor Buck. Los valores están configurados para un vehículo eléctrico (ej. mayor capacidad de batería, menor masa).

*   **`HybridBikeConsumptionModel/parameters_hybrid.py`**:
    Define la clase `HEV` que contiene los parámetros para un **modelo de vehículo híbrido**. Extiende o modifica los parámetros eléctricos y físicos del modelo eléctrico e introduce los **parámetros del motor de combustión interna (ICE)**, carburador y transmisión. Incluye masa, capacidad de batería (menor que la eléctrica pura), inercia del tren motriz (`je`), coeficiente de fricción (`f_sft`), constante de energía del combustible (`hu`), eficiencia térmica (`nu`), propiedades del carburador y relaciones de engranajes de la transmisión (`r1` a `r5`) y la cadena (`rc`), así como el control del embrague (`beta_t`).

*   **`functions.py`**:
    Contiene **funciones auxiliares** utilizadas por el modelo dinámico continuo (`model.py`):
    *   `RK(tsim, dt, x0, delta, hybrid_cont, last_vel)`: Implementa el **integrador numérico Runge-Kutta de cuarto orden (RK4)**. Recibe el estado actual, el vector de control, el paso de tiempo (`dt`) y calcula el estado en el siguiente instante utilizando la función de derivadas (`model`).
    *   `model(t, x, u, hybrid_cont, last_vel, dt)`: Es la **función que calcula las derivadas temporales ($\dot{\mathbf{X}}$)** del vector de estado del vehículo en un instante dado, basándose en el estado actual (`x`), el vector de control (`u`), el modo híbrido (`hybrid_cont`) y parámetros del vehículo. Implementa las ecuaciones físicas de traslación, rotación y circuitos eléctricos/combustión.
    *   `wmtc_profile(ts, tini, tfin, v)`: **Interpola linealmente** un perfil de datos discreto (velocidad o pendiente, `v`), definido en intervalos de 1 segundo, a un perfil muestreado con un paso de tiempo más pequeño (`ts`), adecuado para la resolución del integrador RK4.

*   **`model.py`**:
    Implementa el **modelo dinámico continuo detallado para un *único* vehículo**.
    *   Carga los parámetros relevantes (`HEV` class) según el parámetro de entrada `hybrid_cont` (0 para eléctrico, 1 para híbrido).
    *   Define el vector de estado inicial (`x0`) y la estructura del vector de control (`delta`).
    *   Genera los perfiles de referencia de velocidad y pendiente interpolados usando `wmtc_profile`.
    *   Implementa un **controlador (similar a PID)** para seguir el perfil de velocidad objetivo, ajustando el comando de acelerador (para ICE) o duty cycle (para EM) y el freno. Esta lógica de control incluye **decisiones binarias** para distribuir el esfuerzo entre aceleración y freno, y para saturar los comandos dentro de sus límites.
    *   Define una **lógica de selección de marchas (`gamma`)** como una función escalón discreta de la velocidad (para modo híbrido), y fija la marcha en modo eléctrico.
    *   Utiliza el integrador `RK` para simular la evolución del estado del vehículo a lo largo del tiempo, basado en el modelo de derivadas y los controles calculados.
    *   Retorna el consumo total de potencia eléctrica (último elemento del vector de estado) y la duración total de la simulación. Incluye código comentado para graficar resultados.

*   **`ModeloMoto1.py`**:
    Implementa un **modelo simplificado de "partícula" discreto** para un *único* vehículo.
    *   Carga los parámetros del vehículo (eléctrico o híbrido).
    *   Itera paso a paso a través de los perfiles de velocidad y pendiente de entrada (asumiendo implícitamente $\Delta t = 1$ segundo).
    *   En cada paso, calcula las **fuerzas resistivas** (aerodinámica, rodadura, gravedad) y la **fuerza de inercia** utilizando la diferencia de velocidad con el paso anterior ($\Delta v / \Delta t$).
    *   Estima la potencia requerida y calcula el **consumo de energía/combustible** en ese paso basándose en eficiencias estimadas y el modo de operación.
    *   Realiza un seguimiento del **Estado de Carga (SOC) de la batería**.
    *   Incorpora una **lógica dinámica de recarga**: si el SOC cae por debajo de un `umbral_energia`, activa un estado de recarga (`en_recarga` = True). En este estado, la simulación "pausa" el movimiento (fuerza velocidad y pendiente a cero en los datos de entrada restantes), inicia un contador de tiempo de recarga, identifica la estación más cercana (si se proporcionan posiciones), y al completar el `tiempo_recarga` definido, restaura el SOC al máximo (`E_max`) y la simulación retoma el perfil de ruta desde donde se detuvo. Esta lógica se basa en **decisiones binarias** (`if/elif/else`) que alteran el flujo de simulación y las variables de estado.
    *   Lee datos de rutas (velocidad y pendiente) de un archivo `.pkl`, los procesa (incluyendo interpolación de posiciones) y ejecuta la simulación.
    *   Recopila históricos de SOC y consumo, y genera gráficos y un mapa interactivo (`rutas.html`).

*   **`agentBasedModel.py`**:
    Extiende el modelo de partícula para realizar una **simulación basada en agentes** con **múltiples vehículos** operando concurrentemente.
    *   Define la clase `Moto`, que actúa como **agente**. Cada instancia `Moto` mantiene su propio estado (SOC, posición, ruta asignada, estado de recarga, contadores).
    *   El método `Moto.avanzar_paso()` implementa la lógica de simulación para un agente individual en un paso de tiempo, replicando los cálculos de consumo y la **lógica de recarga** del modelo de partícula, incluyendo la búsqueda de la estación de recarga más cercana de una lista compartida (`estaciones`). Contiene las **decisiones binarias** clave para el cambio de estado del agente (moviéndose vs. recargando).
    *   Utiliza un scheduler simple (`SimpleScheduler`) para coordinar la ejecución del método `avanzar_paso()` para todos los agentes en cada paso de simulación global.
    *   Distribuye los datos de las rutas cargadas (`speed_slope_smooth.pkl`) entre múltiples agentes (concatenando segmentos) para simular una flota que recorre trayectos más largos de forma agregada.
    *   Recopila datos de simulación (histórico de SOC, puntos de recarga realizados) para cada agente.
    *   Genera un mapa (`rutas.html`) que muestra las rutas y los puntos específicos donde cada agente realizó una recarga.
    *   Presenta gráficos mostrando la evolución del SOC para cada agente a lo largo de la simulación.
    *   Incluye un cálculo básico de la **reducción neta de emisiones** comparando el consumo eléctrico/híbrido simulado con una estimación de emisiones si los mismos trayectos se hubieran realizado con un vehículo de combustión equivalente.

## Dependencias

Para ejecutar este código, necesitas tener Python instalado junto con las siguientes librerías. Puedes instalarlas usando pip:

install numpy matplotlib pandas geopy folium osmnx networkx mesa