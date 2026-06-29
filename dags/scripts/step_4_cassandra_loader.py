import json
import os
import time
import pandas as pd
from pymongo import MongoClient

def load_data_to_cassandra(input_path, cassandra_host, **kwargs):
    """
    Sincronización Incremental:
    Consulta los agregados globales directamente de MongoDB (Source of Truth)
    usando pipelines de agregación, limpia (truncates) las tablas analíticas de Cassandra,
    y carga los nuevos totales globales.
    """
    print(f"Iniciando sincronización Cassandra-MongoDB. Host Cassandra: {cassandra_host}")
    
    # Determinar la URI de MongoDB según el host de Cassandra (localhost para local, mongodb para docker)
    if cassandra_host == "localhost":
        mongo_uri = "mongodb://admin:password123@localhost:27017/"
    else:
        mongo_uri = "mongodb://admin:password123@mongodb:27017/"
        
    print(f"[CONEXIÓN] Conectando a MongoDB en: {mongo_uri}")
    
    try:
        # 1. Conectar a MongoDB y obtener agregados
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ping')
        db = mongo_client['nyc_311']
        collection = db['complaints_raw']
        
        total_mongo = collection.count_documents({})
        print(f"MongoDB contiene {total_mongo} registros históricos.")
        
        if total_mongo == 0:
            print("MongoDB está vacío. Nada que sincronizar con Cassandra.")
            mongo_client.close()
            return 0
            
        # Ejecutar los pipelines de agregación en MongoDB
        print("Calculando agregaciones en MongoDB...")
        
        # A. Quejas por día
        pipe_day = [
            {"$group": {"_id": {"$substr": ["$created_date", 0, 10]}, "total": {"$sum": 1}}}
        ]
        agg_day = list(collection.aggregate(pipe_day))
        
        # B. Quejas por distrito (Borough)
        pipe_borough = [
            {"$group": {"_id": "$borough", "total": {"$sum": 1}}}
        ]
        agg_borough = list(collection.aggregate(pipe_borough))
        
        # C. Quejas por tipo
        pipe_type = [
            {"$group": {"_id": "$complaint_type", "total": {"$sum": 1}}}
        ]
        agg_type = list(collection.aggregate(pipe_type))
        
        # D. Quejas por estado
        pipe_status = [
            {"$group": {"_id": "$status", "total": {"$sum": 1}}}
        ]
        agg_status = list(collection.aggregate(pipe_status))
        
        # E. Quejas por agencia y día
        pipe_agency_day = [
            {
                "$group": {
                    "_id": {
                        "agency": "$agency",
                        "date": {"$substr": ["$created_date", 0, 10]}
                    },
                    "total": {"$sum": 1}
                }
            }
        ]
        agg_agency_day = list(collection.aggregate(pipe_agency_day))
        
        mongo_client.close()
        print("Agregaciones calculadas con éxito de MongoDB.")
        
    except Exception as e:
        print(f"Error al conectar o agregar en MongoDB: {e}")
        raise e
        
    # 2. Conectar a Cassandra e insertar los agregados globales
    print(f"[CONEXIÓN] Conectando a Cassandra en: {cassandra_host}")
    try:
        from cassandra.cluster import Cluster
        
        # Conectar con reintentos
        cluster = None
        session = None
        for attempt in range(1, 13):
            try:
                cluster = Cluster([cassandra_host], port=9042)
                session = cluster.connect()
                break
            except Exception as e:
                print(f"Intento {attempt}/12: Reintentando conectar a Cassandra... ({e})")
                time.sleep(5)
        else:
            raise ConnectionError("No se pudo conectar a Cassandra.")
            
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS nyc311_ks 
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
        """)
        session.set_keyspace('nyc311_ks')
        
        # Crear tablas si no existen
        session.execute("CREATE TABLE IF NOT EXISTS complaints_by_day (complaint_date date PRIMARY KEY, total int)")
        session.execute("CREATE TABLE IF NOT EXISTS complaints_by_borough (borough text PRIMARY KEY, total int)")
        session.execute("CREATE TABLE IF NOT EXISTS complaints_by_type (complaint_type text PRIMARY KEY, total int)")
        session.execute("CREATE TABLE IF NOT EXISTS complaints_by_status (status text PRIMARY KEY, total int)")
        session.execute("""
            CREATE TABLE IF NOT EXISTS complaints_by_agency_day (
                agency text,
                complaint_date date,
                total int,
                PRIMARY KEY (agency, complaint_date)
            ) WITH CLUSTERING ORDER BY (complaint_date DESC)
        """)
        
        # Truncar (vaciar) tablas analíticas anteriores para recargar totales actualizados
        print("Limpiando tablas analíticas previas en Cassandra...")
        session.execute("TRUNCATE complaints_by_day")
        session.execute("TRUNCATE complaints_by_borough")
        session.execute("TRUNCATE complaints_by_type")
        session.execute("TRUNCATE complaints_by_status")
        session.execute("TRUNCATE complaints_by_agency_day")
        
        # Insertar los nuevos datos agregados globales
        print("Cargando nuevos agregados globales en Cassandra...")
        
        # complaints_by_day
        stmt_day = session.prepare("INSERT INTO complaints_by_day (complaint_date, total) VALUES (?, ?)")
        for row in agg_day:
            date_val = pd.to_datetime(row['_id']).date() if row['_id'] else pd.to_datetime('1970-01-01').date()
            session.execute(stmt_day, (date_val, int(row['total'])))
            
        # complaints_by_borough
        stmt_borough = session.prepare("INSERT INTO complaints_by_borough (borough, total) VALUES (?, ?)")
        for row in agg_borough:
            borough_val = row['_id'] if row['_id'] else 'UNSPECIFIED'
            session.execute(stmt_borough, (borough_val, int(row['total'])))
            
        # complaints_by_type
        stmt_type = session.prepare("INSERT INTO complaints_by_type (complaint_type, total) VALUES (?, ?)")
        for row in agg_type:
            type_val = row['_id'] if row['_id'] else 'UNSPECIFIED'
            session.execute(stmt_type, (type_val, int(row['total'])))
            
        # complaints_by_status
        stmt_status = session.prepare("INSERT INTO complaints_by_status (status, total) VALUES (?, ?)")
        for row in agg_status:
            status_val = row['_id'] if row['_id'] else 'Open'
            session.execute(stmt_status, (status_val, int(row['total'])))
            
        # complaints_by_agency_day
        stmt_agency_day = session.prepare("INSERT INTO complaints_by_agency_day (agency, complaint_date, total) VALUES (?, ?, ?)")
        for row in agg_agency_day:
            agency_val = row['_id']['agency'] if row['_id']['agency'] else 'UNSPECIFIED'
            date_val = pd.to_datetime(row['_id']['date']).date() if row['_id']['date'] else pd.to_datetime('1970-01-01').date()
            session.execute(stmt_agency_day, (agency_val, date_val, int(row['total'])))
            
        print("Cassandra: Sincronización analítica completada exitosamente.")
        cluster.shutdown()
        
    except ImportError:
        print("[AVISO] 'cassandra-driver' no instalado. Saltando carga real en Cassandra.")
    except Exception as e:
        print(f"Error al conectar o cargar en Cassandra: {e}")
        raise e
        
    return total_mongo
