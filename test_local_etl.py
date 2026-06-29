import os
import sys

# Agregar la carpeta dags al PATH de Python para poder importar los módulos localmente
sys.path.append(os.path.join(os.path.dirname(__file__), 'dags'))

from scripts.step_1_extractor import extract_raw_data
from scripts.step_2_cleaner import clean_extracted_data
from scripts.step_6_kpi_generator import calculate_and_save_kpis

# Simular las llamadas de los loaders para verificar firmas
from scripts.step_3_mongo_loader import load_data_to_mongo
from scripts.step_4_cassandra_loader import load_data_to_cassandra
from scripts.step_5_neo4j_loader import load_data_to_neo4j

def run_local_test():
    print("--- INICIANDO PRUEBA DE ETL LOCAL ---")
    
    # Rutas locales
    import glob
    raw_data_dir = './data/raw/'
    extracted_path = './data/extracted_raw.json'
    cleaned_path = './data/cleaned_data.json'
    
    # Verificar si existen archivos .jsonl en la landing zone
    jsonl_files = glob.glob(os.path.join(raw_data_dir, "*.jsonl"))
    if not jsonl_files:
        print(f"Error: No se encontraron archivos .jsonl en la carpeta '{raw_data_dir}'.")
        print("Por favor, coloca archivos .jsonl en la landing zone para procesar.")
        return
        
    # 1. Ejecutar Extracción
    try:
        extracted_count = extract_raw_data(os.path.join(raw_data_dir, "dummy.jsonl"), extracted_path)
        print(f" Extracción completada. {extracted_count} registros guardados en temporal.")
    except Exception as e:
        print(f"Error en Extracción: {e}")
        return

    # 2. Ejecutar Limpieza y Validación
    try:
        cleaned_count = clean_extracted_data(extracted_path, cleaned_path)
        print(f" Limpieza y validación completadas. {cleaned_count} registros válidos.")
    except Exception as e:
        print(f" Error en Limpieza: {e}")
        return

    # 3. Simular Cargas (para ver que no tiren error de importación)
    print("\n--- Simulando cargas a bases de datos (si no están instalados los drivers) ---")
    load_data_to_mongo(cleaned_path, "mongodb://admin:password123@localhost:27017/")
    load_data_to_cassandra(cleaned_path, "localhost")
    load_data_to_neo4j(cleaned_path, "bolt://localhost:7687", "neo4j", "password123")

    # 4. Ejecutar KPIs
    print("\n--- Calculando Indicadores (KPIs) ---")
    try:
        kpis_success = calculate_and_save_kpis()
        if kpis_success:
            print(" KPIs generados exitosamente en 'data/kpi_report.json'.")
    except Exception as e:
        print(f" Error en generación de KPIs: {e}")

    print("\n--- PRUEBA COMPLETADA CON ÉXITO ---")

if __name__ == '__main__':
    run_local_test()
