import json
import os
import glob
import shutil
from datetime import datetime

def extract_raw_data(input_path, output_path, **kwargs):
    """
    Landing Zone Extractor:
    Busca todos los archivos .jsonl en la carpeta de entrada (raw data),
    extrae sus registros combinándolos, y archiva los procesados en 'data/processed/'.
    """
    input_dir = os.path.dirname(input_path)
    print(f"Iniciando escaneo de landing zone en: {input_dir}")
    
    # Buscar todos los archivos .jsonl en el directorio de entrada
    jsonl_files = glob.glob(os.path.join(input_dir, "*.jsonl"))
    
    if not jsonl_files:
        print("No se encontraron nuevos archivos .jsonl en la landing zone para procesar.")
        # Escribir archivo de salida vacío para no quebrar las siguientes etapas del DAG
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump([], outfile)
        return 0
        
    print(f"Archivos encontrados para procesar: {jsonl_files}")
    records = []
    
    for file_path in jsonl_files:
        print(f"Procesando archivo: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as infile:
            for line in infile:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] Error al decodificar JSON en la línea: {line}. Saltando. ({e})")
                        
    # Asegurar que el directorio de salida exista
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(records, outfile, indent=2)
        
    print(f"Extracción completada. Se extrajeron {len(records)} registros en total.")
    
    # Archivar los archivos procesados para dejar la landing zone limpia
    processed_dir = os.path.join(os.path.dirname(input_dir), "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for file_path in jsonl_files:
        filename = os.path.basename(file_path)
        archive_name = f"{timestamp}_{filename}"
        dest_path = os.path.join(processed_dir, archive_name)
        try:
            shutil.move(file_path, dest_path)
            print(f"Archivo archivado con éxito: {file_path} -> {dest_path}")
        except Exception as e:
            print(f"[ERROR] No se pudo archivar el archivo {file_path}: {e}")
            
    return len(records)
