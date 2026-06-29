#!/usr/bin/env python3
import sys
from neo4j import GraphDatabase

def run_crud_demo():
    neo4j_uri = "bolt://localhost:7687"
    neo4j_user = "neo4j"
    neo4j_password = "password123"
    
    print(f"Conectando a Neo4j en {neo4j_uri}...")
    
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        # Verificar la conexión
        with driver.session() as session:
            session.run("RETURN 1")
            
        print("¡Conectado exitosamente a Neo4j!")
        
        with driver.session() as session:
            # Limpiar cualquier residuo de pruebas previas
            session.run("MATCH (n:ServiceRequest {unique_key: 999999}) DETACH DELETE n")
            session.run("MATCH (n:Agency {agency: 'TEST_AGENCY'}) DETACH DELETE n")
            
            # 1. CREATE (Crear nodos y relación)
            print("\n--- 1. OPERACIÓN CREATE ---")
            create_query = """
            CREATE (sr:ServiceRequest {
                unique_key: 999999,
                created_date: '2026-06-25T12:00:00',
                status: 'Open',
                borough: 'BROOKLYN'
            })
            CREATE (ag:Agency {
                agency: 'TEST_AGENCY',
                name: 'Test agency department'
            })
            CREATE (sr)-[r:HANDLED_BY]->(ag)
            RETURN sr, ag, r
            """
            result = session.run(create_query)
            record = result.single()
            if record:
                print("¡Nodos de ServiceRequest y Agency creados y relacionados con HANDLED_BY!")
                print(f"ServiceRequest: {record['sr']}")
                print(f"Agency: {record['ag']}")
                
            # 2. READ (Consultar nodos y relación)
            print("\n--- 2. OPERACIÓN READ ---")
            read_query = """
            MATCH (sr:ServiceRequest {unique_key: 999999})-[r:HANDLED_BY]->(ag:Agency {agency: 'TEST_AGENCY'})
            RETURN sr.unique_key AS unique_key, sr.status AS status, ag.name AS agency_name
            """
            result = session.run(read_query)
            record = result.single()
            if record:
                print("Relación encontrada en la base de datos:")
                print(f"  Incident ID: {record['unique_key']}")
                print(f"  Status: {record['status']}")
                print(f"  Handled by Agency: {record['agency_name']}")
                
            # 3. UPDATE (Actualizar propiedades)
            print("\n--- 3. OPERACIÓN UPDATE ---")
            update_query = """
            MATCH (sr:ServiceRequest {unique_key: 999999})
            SET sr.status = 'Closed', sr.resolved_date = '2026-06-26T08:00:00'
            RETURN sr.unique_key AS unique_key, sr.status AS status
            """
            result = session.run(update_query)
            record = result.single()
            if record:
                print(f"Registro actualizado. ID: {record['unique_key']}, Nuevo Status: {record['status']}")
                
            # 4. DELETE (Eliminar nodos y relaciones)
            print("\n--- 4. OPERACIÓN DELETE ---")
            delete_query = """
            MATCH (sr:ServiceRequest {unique_key: 999999})
            DETACH DELETE sr
            """
            session.run(delete_query)
            print("Nodo ServiceRequest y sus relaciones eliminados.")
            
            # Limpiar también la agencia de prueba
            session.run("MATCH (ag:Agency {agency: 'TEST_AGENCY'}) DETACH DELETE ag")
            print("Nodo Agency de prueba eliminado.")
            
            # Verificar eliminación
            verify_query = "MATCH (sr:ServiceRequest {unique_key: 999999}) RETURN sr"
            result = session.run(verify_query)
            if result.single() is None:
                print("Verificación: El nodo de prueba fue eliminado con éxito.")
            else:
                print("Error: El nodo de prueba aún existe.")
                
        driver.close()
        
    except Exception as e:
        print(f"Error al ejecutar operaciones CRUD en Neo4j: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_crud_demo()
