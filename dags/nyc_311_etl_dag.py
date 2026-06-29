from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Importación de los scripts modulares de la carpeta dags/scripts
from scripts.step_1_extractor import extract_raw_data
from scripts.step_2_cleaner import clean_extracted_data
from scripts.step_3_mongo_loader import load_data_to_mongo
from scripts.step_4_cassandra_loader import load_data_to_cassandra
from scripts.step_5_neo4j_loader import load_data_to_neo4j
from scripts.step_6_kpi_generator import calculate_and_save_kpis

# Argumentos por defecto del DAG
default_args = {
    'owner': 'grupo_big_data',
    'depends_on_past': False,
    'start_date': datetime(2026, 6, 20),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definición del DAG
with DAG(
    'nyc_311_etl_pipeline',
    default_args=default_args,
    description='Pipeline ETL multimodelo para el dataset NYC 311',
    schedule_interval='@daily',  # Se ejecuta de forma programada diariamente
    catchup=False,
) as dag:

    # Extracción de datos
    task_extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_raw_data,
        op_kwargs={
            'input_path': '/opt/airflow/data/raw/nyc_311_raw_75k.jsonl',
            'output_path': '/opt/airflow/data/extracted_raw.json'
        }
    )

    # Validación y limpieza
    task_clean = PythonOperator(
        task_id='validate_and_clean',
        python_callable=clean_extracted_data,
        op_kwargs={
            'input_path': '/opt/airflow/data/extracted_raw.json',
            'output_path': '/opt/airflow/data/cleaned_data.json'
        }
    )

    # Carga en MongoDB
    task_load_mongo = PythonOperator(
        task_id='load_to_mongodb',
        python_callable=load_data_to_mongo,
        op_kwargs={
            'input_path': '/opt/airflow/data/cleaned_data.json',
            'mongo_uri': 'mongodb://admin:password123@mongodb:27017/'
        }
    )

    # Transformación y carga en Cassandra
    task_load_cassandra = PythonOperator(
        task_id='load_to_cassandra',
        python_callable=load_data_to_cassandra,
        op_kwargs={
            'input_path': '/opt/airflow/data/cleaned_data.json',
            'cassandra_host': 'cassandra'
        }
    )

    # Construcción de relaciones y carga en Neo4j
    task_load_neo4j = PythonOperator(
        task_id='load_to_neo4j',
        python_callable=load_data_to_neo4j,
        op_kwargs={
            'input_path': '/opt/airflow/data/cleaned_data.json',
            'neo4j_uri': 'bolt://neo4j:7687',
            'neo4j_user': 'neo4j',
            'neo4j_password': 'password123'
        }
    )

    # Generación automática de indicadores (KPIs)
    task_generate_kpis = PythonOperator(
        task_id='generate_kpis',
        python_callable=calculate_and_save_kpis,
        op_kwargs={
            'mongo_uri': 'mongodb://admin:password123@mongodb:27017/',
            'cassandra_host': 'cassandra',
            'neo4j_uri': 'bolt://neo4j:7687',
            'neo4j_user': 'neo4j',
            'neo4j_password': 'password123'
        }
    )

    # Definición del flujo de ejecución (Dependencias)
    task_extract >> task_clean >> task_load_mongo
    task_load_mongo >> [task_load_cassandra, task_load_neo4j]
    [task_load_cassandra, task_load_neo4j] >> task_generate_kpis
