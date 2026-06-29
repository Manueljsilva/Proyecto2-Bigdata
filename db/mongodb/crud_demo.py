#!/usr/bin/env python3
import sys
from pymongo import MongoClient

def run_crud_demo():
    mongo_uri = "mongodb://admin:password123@localhost:27017/"
    print(f"Conectando a MongoDB en {mongo_uri}...")
    
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client['nyc_311']
        collection = db['complaints_raw']
        
        # Test connection
        client.admin.command('ping')
        print("¡Conectado exitosamente a MongoDB!")
        
        # 1. CREATE (InsertOne)
        print("\n--- 1. OPERACIÓN CREATE ---")
        test_doc = {
            "unique_key": "TEST001",
            "created_date": "2026-06-24T00:00:00.000",
            "agency": "TEST",
            "complaint_type": "Prueba MongoDB",
            "borough": "QUEENS",
            "status": "Open",
            "descriptor": "Test Descriptor",
            "open_data_channel_type": "ONLINE"
        }
        # Asegurar que no exista previamente
        collection.delete_one({"unique_key": "TEST001"})
        
        result = collection.insert_one(test_doc)
        print(f"Documento insertado con _id: {result.inserted_id}")
        
        # 2. READ (FindOne)
        print("\n--- 2. OPERACIÓN READ ---")
        doc = collection.find_one({"unique_key": "TEST001"})
        print("Documento encontrado:")
        print(doc)
        
        # 3. UPDATE (UpdateOne)
        print("\n--- 3. OPERACIÓN UPDATE ---")
        update_result = collection.update_one(
            {"unique_key": "TEST001"},
            {"$set": {"status": "Closed"}}
        )
        print(f"Documentos modificados: {update_result.modified_count}")
        updated_doc = collection.find_one({"unique_key": "TEST001"})
        print("Documento después de actualizar:")
        print(updated_doc)
        
        # 4. DELETE (DeleteOne)
        print("\n--- 4. OPERACIÓN DELETE ---")
        delete_result = collection.delete_one({"unique_key": "TEST001"})
        print(f"Documentos eliminados: {delete_result.deleted_count}")
        
        # Verificar eliminación
        deleted_doc = collection.find_one({"unique_key": "TEST001"})
        if deleted_doc is None:
            print("El documento fue eliminado exitosamente.")
        else:
            print("Error: El documento aún existe.")
            
        client.close()
        
    except Exception as e:
        print(f"Error al ejecutar operaciones CRUD en MongoDB: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_crud_demo()
