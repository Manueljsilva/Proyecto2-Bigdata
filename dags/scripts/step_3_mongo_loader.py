import json
import os
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

def load_data_to_mongo(input_path, mongo_uri, **kwargs):
    """
    Carga incremental:
    Añade el dataset limpio en la colección 'complaints_raw' sin borrar los históricos,
    ignorando colisiones de claves duplicadas mediante inserciones desordenadas (ordered=False).
    """
    print(f"Iniciando carga incremental a MongoDB desde: {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró el archivo limpio en {input_path}")
        
    with open(input_path, 'r', encoding='utf-8') as infile:
        cleaned_records = json.load(infile)
        
    if not cleaned_records:
        print("No hay registros para insertar en esta ejecución.")
        return 0
        
    print(f"[CONEXIÓN] Intentando conectar a MongoDB con URI: {mongo_uri}")
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db = client['nyc_311']
        collection = db['complaints_raw']
        
        # Crear los índices analíticos requeridos si no existen
        print("Asegurando índices en MongoDB...")
        collection.create_index("unique_key", unique=True)
        collection.create_index("created_date")
        collection.create_index("complaint_type")
        collection.create_index("borough")
        collection.create_index("status")
        collection.create_index("agency")
        
        batch_size = 5000
        inserted_count = 0
        duplicate_count = 0
        
        print("Insertando registros incrementales...")
        for i in range(0, len(cleaned_records), batch_size):
            batch = cleaned_records[i:i+batch_size]
            try:
                # ordered=False permite que continúe insertando aunque haya fallos de claves duplicadas
                result = collection.insert_many(batch, ordered=False)
                inserted_count += len(result.inserted_ids)
            except BulkWriteError as bwe:
                inserted_count += bwe.details.get('nInserted', 0)
                write_errors = bwe.details.get('writeErrors', [])
                # Filtrar errores que NO sean de clave duplicada (código 11000)
                non_dup_errors = [e for e in write_errors if e.get('code') != 11000]
                if non_dup_errors:
                    raise bwe
                duplicate_count += len(write_errors)
                
            processed = min(i + batch_size, len(cleaned_records))
            print(f"MongoDB: Procesados {processed}/{len(cleaned_records)} documentos...")
            
        print(f"MongoDB: Carga completada. Nuevos insertados: {inserted_count}, Duplicados omitidos: {duplicate_count}")
        client.close()
        
    except Exception as e:
        print(f"Error al conectar o cargar en MongoDB: {e}")
        raise e
        
    return inserted_count
