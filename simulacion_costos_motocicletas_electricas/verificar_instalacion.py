#!/usr/bin/env python3
"""
Script de verificación para asegurar que todos los archivos necesarios están presentes.
"""

import os
import sys

def verificar_archivo(ruta, descripcion):
    """Verifica si un archivo existe."""
    if os.path.exists(ruta):
        print(f"✓ {descripcion}: {ruta}")
        return True
    else:
        print(f"✗ FALTA: {descripcion}: {ruta}")
        return False

def verificar_carpeta(ruta, descripcion):
    """Verifica si una carpeta existe."""
    if os.path.isdir(ruta):
        print(f"✓ {descripcion}: {ruta}")
        return True
    else:
        print(f"✗ FALTA: {descripcion}: {ruta}")
        return False

def main():
    print("="*70)
    print("VERIFICACIÓN DE ARCHIVOS NECESARIOS")
    print("="*70)
    print()
    
    errores = []
    
    # Verificar script principal
    print("📄 Archivos principales:")
    if not verificar_archivo("calcular_costo_viaje_aleatorio.py", "Script principal"):
        errores.append("Script principal no encontrado")
    print()
    
    # Verificar carpeta del modelo
    print("📁 Carpeta del modelo:")
    if not verificar_carpeta("modelo_motocicleta_electrica", "Carpeta del modelo"):
        errores.append("Carpeta 'modelo_motocicleta_electrica' no encontrada")
    else:
        if not verificar_archivo("modelo_motocicleta_electrica/procesar_rutas.py", "Módulo procesar_rutas"):
            errores.append("Módulo procesar_rutas.py no encontrado")
        if not verificar_carpeta("modelo_motocicleta_electrica/HybridBikeConsumptionModel", "Carpeta de parámetros"):
            errores.append("Carpeta HybridBikeConsumptionModel no encontrada")
    print()
    
    # Verificar shapefiles
    print("🗺️  Shapefiles:")
    shapefiles_zonas = ["ZONAS SIT.shp", "ZONAS SIT.shx", "ZONAS SIT.dbf", "ZONAS SIT.prj"]
    for shp in shapefiles_zonas:
        if not verificar_archivo(shp, f"Shapefile ZONAS SIT ({shp})"):
            errores.append(f"Shapefile ZONAS SIT incompleto: falta {shp}")
    
    shapefiles_zat = ["zat.shp", "zat.shx", "zat.dbf", "zat.prj"]
    for shp in shapefiles_zat:
        if not verificar_archivo(shp, f"Shapefile ZAT ({shp})"):
            errores.append(f"Shapefile ZAT incompleto: falta {shp}")
    print()
    
    # Verificar datos
    print("📊 Archivos de datos:")
    if not verificar_archivo("ENPH_Rev.xlsx", "Datos de canasta familiar"):
        errores.append("Archivo ENPH_Rev.xlsx no encontrado")
    if not verificar_archivo("viajes_motos_procesados.csv", "Base de datos de viajes"):
        errores.append("Archivo viajes_motos_procesados.csv no encontrado")
    print()
    
    # Verificar dependencias
    print("📦 Verificando dependencias de Python:")
    dependencias = [
        "pandas", "numpy", "geopandas", "matplotlib", 
        "geopy", "requests", "folium", "openpyxl", "scipy"
    ]
    
    faltantes = []
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} - NO INSTALADO")
            faltantes.append(dep)
    
    if faltantes:
        print()
        print("⚠️  Para instalar las dependencias faltantes, ejecuta:")
        print("   pip install -r requirements.txt")
        errores.append(f"Dependencias faltantes: {', '.join(faltantes)}")
    print()
    
    # Resumen
    print("="*70)
    if errores:
        print("❌ VERIFICACIÓN FALLIDA")
        print()
        print("Errores encontrados:")
        for error in errores:
            print(f"  - {error}")
        print()
        sys.exit(1)
    else:
        print("✅ VERIFICACIÓN EXITOSA")
        print()
        print("Todos los archivos necesarios están presentes.")
        print("Puedes ejecutar la simulación con:")
        print("   python calcular_costo_viaje_aleatorio.py")
        print()
        sys.exit(0)

if __name__ == "__main__":
    main()

