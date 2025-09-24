import pickle

# Abrir el archivo en modo lectura binaria
with open('speed_slope_smooth.pkl', 'rb') as file:
    data = pickle.load(file)

# Mostrar el tipo de dato y el contenido cargado
print("Tipo de dato:", type(data))
print("Contenido:")
print(data)
