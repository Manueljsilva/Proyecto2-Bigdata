# Orquestación con Apache Airflow

Esta carpeta contiene la definición del DAG de Airflow y los scripts ETL modulares.

## Estructura
* `nyc_311_etl_dag.py`: Define la estructura del DAG, las tareas (tasks), el orden de ejecución y los operadores.
* `scripts/`: Módulos de Python que implementan la lógica de negocio de cada tarea:
  - `step_1_extractor.py`: Lee el archivo JSONL original de `data/raw/`.
  - `step_2_cleaner.py`: Limpia los tipos de datos, fechas, nulos, etc.
  - `step_3_mongo_loader.py`: Inserta los documentos limpios en MongoDB.
  - `step_4_cassandra_loader.py`: Transforma los registros y los guarda en Cassandra.
  - `step_5_neo4j_loader.py`: Crea los nodos y relaciones en Neo4j.
  - `step_6_kpi_generator.py`: Genera y guarda los KPIs agregados.
