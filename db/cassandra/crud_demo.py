#!/usr/bin/env python3
import sys
import time
# pyrefly: ignore [missing-import]
from cassandra.cluster import Cluster

def run_crud_demo():
    cassandra_host = "localhost"
    print(f"Conectando a Cassandra en {cassandra_host}...")
    
    try:
        cluster = Cluster([cassandra_host], port=9042)
        session = cluster.connect()
        
        # Asegurar que el keyspace y la tabla existan para la demo
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS nyc311_ks 
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
        """)
        session.set_keyspace('nyc311_ks')
        
        session.execute("""
            CREATE TABLE IF NOT EXISTS complaints_by_borough (
                borough text PRIMARY KEY,
                total int
            )
        """)
        
        print("¡Conectado exitosamente a Cassandra!")
        
        # 1. CREATE (Insert)
        print("\n--- 1. OPERACIÓN CREATE ---")
        insert_query = "INSERT INTO complaints_by_borough (borough, total) VALUES (%s, %s)"
        session.execute(insert_query, ('TEST_BOROUGH', 100))
        print("Registro insertado: ('TEST_BOROUGH', 100)")
        
        # 2. READ (Select)
        print("\n--- 2. OPERACIÓN READ ---")
        select_query = "SELECT * FROM complaints_by_borough WHERE borough = %s"
        rows = list(session.execute(select_query, ('TEST_BOROUGH',)))
        print("Registro encontrado:")
        for r in rows:
            print(f"Borough: {r.borough}, Total: {r.total}")
            
        # 3. UPDATE (Update)
        print("\n--- 3. OPERACIÓN UPDATE ---")
        update_query = "UPDATE complaints_by_borough SET total = %s WHERE borough = %s"
        session.execute(update_query, (150, 'TEST_BOROUGH'))
        print("Registro actualizado a total = 150")
        
        rows_updated = list(session.execute(select_query, ('TEST_BOROUGH',)))
        print("Registro después de actualizar:")
        for r in rows_updated:
            print(f"Borough: {r.borough}, Total: {r.total}")
            
        # 4. DELETE (Delete)
        print("\n--- 4. OPERACIÓN DELETE ---")
        delete_query = "DELETE FROM complaints_by_borough WHERE borough = %s"
        session.execute(delete_query, ('TEST_BOROUGH',))
        print("Registro eliminado para 'TEST_BOROUGH'")
        
        # Verificar eliminación
        rows_deleted = list(session.execute(select_query, ('TEST_BOROUGH',)))
        if len(rows_deleted) == 0:
            print("El registro fue eliminado exitosamente.")
        else:
            print("Error: El registro aún existe.")
            
        cluster.shutdown()
        
    except Exception as e:
        print(f"Error al ejecutar operaciones CRUD en Cassandra: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_crud_demo()
