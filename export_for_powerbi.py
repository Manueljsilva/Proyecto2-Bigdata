#!/usr/bin/env python3
"""
export_for_powerbi.py
=====================
Exporta los datos de las 3 bases de datos (MongoDB, Cassandra, Neo4j)
a archivos CSV listos para consumir en Power BI Desktop.

Uso:
    python export_for_powerbi.py

Los CSV se guardan en la carpeta ./exports/
"""

import os
import sys
import pandas as pd
from datetime import datetime

# ──────────────────────────────────────────────
# CONFIGURACIÓN DE CONEXIONES (localhost = Docker expuesto)
# ──────────────────────────────────────────────
MONGO_URI       = os.getenv("MONGO_URI",      "mongodb://admin:password123@localhost:27017/")
CASSANDRA_HOST  = os.getenv("CASSANDRA_HOST", "localhost")
NEO4J_URI       = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER      = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD  = os.getenv("NEO4J_PASSWORD", "password123")

EXPORTS_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

def save_csv(df: pd.DataFrame, filename: str):
    """Guarda un DataFrame como CSV en la carpeta exports/ e imprime resumen."""
    path = os.path.join(EXPORTS_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")  # utf-8-sig para compatibilidad con Excel/Power BI
    print(f"  ✅ {filename}  ({len(df):,} filas)  →  {path}")

# ══════════════════════════════════════════════
# 1. EXPORTAR DESDE CASSANDRA
# ══════════════════════════════════════════════
def export_cassandra():
    print("\n Exportando desde Cassandra...")
    try:
        from cassandra.cluster import Cluster

        cluster = Cluster([CASSANDRA_HOST], port=9042)
        session = cluster.connect()
        session.set_keyspace("nyc311_ks")

        # Tabla 1: quejas por día
        rows = session.execute("SELECT complaint_date, total FROM complaints_by_day")
        df = pd.DataFrame(list(rows), columns=["complaint_date", "total"])
        df["complaint_date"] = pd.to_datetime(df["complaint_date"].astype(str))
        df = df.sort_values("complaint_date")
        save_csv(df, "powerbi_complaints_by_day.csv")

        # Tabla 2: quejas por borough
        rows = session.execute("SELECT borough, total FROM complaints_by_borough")
        df = pd.DataFrame(list(rows), columns=["borough", "total"])
        df = df.sort_values("total", ascending=False)
        save_csv(df, "powerbi_complaints_by_borough.csv")

        # Tabla 3: quejas por tipo
        rows = session.execute("SELECT complaint_type, total FROM complaints_by_type")
        df = pd.DataFrame(list(rows), columns=["complaint_type", "total"])
        df = df.sort_values("total", ascending=False)
        save_csv(df, "powerbi_complaints_by_type.csv")

        # Tabla 4: quejas por estado
        rows = session.execute("SELECT status, total FROM complaints_by_status")
        df = pd.DataFrame(list(rows), columns=["status", "total"])
        df = df.sort_values("total", ascending=False)
        save_csv(df, "powerbi_complaints_by_status.csv")

        # Tabla 5: quejas por agencia y día
        rows = session.execute("SELECT agency, complaint_date, total FROM complaints_by_agency_day")
        df = pd.DataFrame(list(rows), columns=["agency", "complaint_date", "total"])
        df["complaint_date"] = pd.to_datetime(df["complaint_date"].astype(str))
        df = df.sort_values(["agency", "complaint_date"])
        save_csv(df, "powerbi_complaints_by_agency_day.csv")

        cluster.shutdown()
        print("  Cassandra: exportación completa.")

    except ImportError:
        print("cassandra-driver no instalado. Instala con: pip install cassandra-driver")
    except Exception as e:
        print(f"Error en Cassandra: {e}")

# ══════════════════════════════════════════════
# 2. EXPORTAR DESDE MONGODB
# ══════════════════════════════════════════════
def export_mongodb():
    print("\n Exportando desde MongoDB...")
    try:
        from pymongo import MongoClient

        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client["nyc_311"]
        collection = db["complaints_raw"]

        total = collection.count_documents({})
        print(f"  MongoDB contiene {total:,} documentos en total.")

        # Exportar muestra completa (o todos si caben en memoria)
        # Proyección: solo los campos más relevantes para Power BI
        projection = {
            "_id": 0,
            "unique_key": 1,
            "created_date": 1,
            "closed_date": 1,
            "agency": 1,
            "complaint_type": 1,
            "descriptor": 1,
            "status": 1,
            "borough": 1,
            "city": 1,
            "open_data_channel_type": 1,
            "latitude": 1,
            "longitude": 1,
        }

        # Limitar a 50,000 filas para no saturar Power BI (ajusta si quieres más)
        limit = min(total, 50_000)
        print(f"  Exportando {limit:,} documentos (ajusta el límite en el script si necesitas más)...")
        docs = list(collection.find({}, projection).limit(limit))
        df = pd.DataFrame(docs)

        # Normalizar fechas
        for col in ["created_date", "closed_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        save_csv(df, "powerbi_mongo_sample.csv")
        client.close()
        print("  MongoDB: exportación completa.")

    except ImportError:
        print(" pymongo no instalado. Instala con: pip install pymongo")
    except Exception as e:
        print(f" Error en MongoDB: {e}")

# ══════════════════════════════════════════════
# 3. EXPORTAR DESDE NEO4J
# ══════════════════════════════════════════════
def export_neo4j():
    print("\n📦 Exportando desde Neo4j...")
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            session.run("RETURN 1")  # ping

        # ── Exportar nodos ──────────────────────────────
        with driver.session() as session:
            query_nodes = """
            MATCH (n)
            RETURN
                labels(n)[0]                                                        AS tipo_nodo,
                coalesce(
                    n.agency,
                    n.complaint_type,
                    n.descriptor_id,
                    n.borough,
                    n.open_data_channel_type,
                    toString(n.unique_key)
                )                                                                   AS nombre,
                count { (n)--() }                                                   AS grado_conexion
            ORDER BY grado_conexion DESC
            """
            result = session.run(query_nodes)
            df_nodes = pd.DataFrame([dict(r) for r in result])

        save_csv(df_nodes, "powerbi_neo4j_nodes.csv")

        # ── Exportar relaciones ─────────────────────────
        with driver.session() as session:
            query_rels = """
            MATCH (a)-[r]->(b)
            RETURN
                labels(a)[0]                                                        AS origen_tipo,
                coalesce(
                    a.agency,
                    a.complaint_type,
                    a.descriptor_id,
                    a.borough,
                    a.open_data_channel_type,
                    toString(a.unique_key)
                )                                                                   AS origen_nombre,
                type(r)                                                             AS tipo_relacion,
                labels(b)[0]                                                        AS destino_tipo,
                coalesce(
                    b.agency,
                    b.complaint_type,
                    b.descriptor_id,
                    b.borough,
                    b.open_data_channel_type,
                    toString(b.unique_key)
                )                                                                   AS destino_nombre
            LIMIT 100000
            """
            result = session.run(query_rels)
            df_rels = pd.DataFrame([dict(r) for r in result])

        save_csv(df_rels, "powerbi_neo4j_relationships.csv")
        driver.close()
        print("  Neo4j: exportación completa.")

    except ImportError:
        print(" neo4j no instalado. Instala con: pip install neo4j")
    except Exception as e:
        print(f" Error en Neo4j: {e}")

# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  NYC 311 — Exportador para Power BI")
    print(f"  Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    export_cassandra()
    export_mongodb()
    export_neo4j()

    print("\n" + "=" * 60)
    print(f"  Exportación finalizada. Archivos en: {EXPORTS_DIR}")
    print("=" * 60)
