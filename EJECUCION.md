# Guía de Ejecución: Proyecto II (Arquitectura Multimodelo y Automatización)

Este documento detalla la arquitectura implementada y los pasos necesarios para configurar, ejecutar y validar el proyecto completo de Big Data utilizando el dataset **NYC 311 Service Requests**.

---

## Resumen de la Implementación

El proyecto se diseñó como un pipeline de datos automatizado y multimodelo, integrando tres bases de datos diferentes, cada una optimizada para un caso de uso particular:

1. **MongoDB (Base de Datos Documental)**:
   - **Propósito**: Almacenar la información cruda completa del incidente (JSON semiestructurado) para consultas flexibles y búsquedas completas.
   - **Colección**: `complaints_raw` dentro de la base de datos `nyc_311`.
   - **Índices**: Se crearon índices en los campos más consultados: `unique_key` (único), `created_date`, `complaint_type`, `borough`, `status` y `agency` para garantizar un rendimiento óptimo.

2. **Apache Cassandra (Base de Datos Columnar)**:
   - **Propósito**: Optimizar consultas analíticas masivas y análisis de series temporales.
   - **Keyspace**: `nyc311_ks`.
   - **Tablas**:
     - `complaints_by_day`: Total de quejas agrupadas por fecha.
     - `complaints_by_borough`: Total de quejas por distrito.
     - `complaints_by_type`: Total de quejas por tipo.
     - `complaints_by_status`: Total de quejas por estado de resolución.
     - `complaints_by_agency_day`: Distribución temporal de quejas por agencia y día.
   - **Carga**: La agregación de los ~80,000 registros se realiza eficientemente en memoria utilizando Python (Pandas), cargando los resultados agregados mediante sentencias preparadas en Cassandra.

3. **Neo4j (Base de Datos de Grafos)**:
   - **Propósito**: Modelar y analizar las relaciones entre entidades clave del sistema.
   - **Nodos**: `ServiceRequest` (Caso), `Agency` (Agencia), `ComplaintType` (Tipo de queja), `Descriptor` (Detalle), `Borough` (Distrito) y `Channel` (Canal de reporte).
   - **Relaciones**:
     - `ServiceRequest` -[:`HANDLED_BY`]-> `Agency`
     - `ServiceRequest` -[:`HAS_COMPLAINT_TYPE`]-> `ComplaintType`
     - `ServiceRequest` -[:`HAS_DESCRIPTOR`]-> `Descriptor`
     - `ServiceRequest` -[:`OCCURRED_IN_BOROUGH`]-> `Borough`
     - `ServiceRequest` -[:`REPORTED_THROUGHs`]-> `Channel` (con metadatos)
     - `Descriptor` -[:`BELONGS_TO_TYPE`]-> `ComplaintType`
   - **Carga**: Construcción del grafo de 25,000 incidentes en transacciones rápidas mediante parameterized `UNWIND` de Cypher.

4. **Apache Airflow (Orquestador)**:
   - **Propósito**: Programar y secuenciar de forma segura cada fase del ETL.
   - **DAG**: `nyc_311_etl_pipeline` en `dags/nyc_311_etl_dag.py`.
   - **Flujo**: Extracción ➔ Limpieza y Deduplicación ➔ Carga MongoDB ➔ Cargas simultáneas a Cassandra y Neo4j ➔ Generación de Reporte JSON de KPIs.

5. **Power BI (Dashboard Analítico)**:
   - **Propósito**: Visualización ejecutiva de KPIs e indicadores del dataset NYC 311.
   - **Fuente de datos**: Archivos CSV generados automáticamente por `export_for_powerbi.py` y almacenados en la carpeta `exports/`.
   - **Archivos exportados**:
     - `powerbi_complaints_by_day.csv` — series temporales desde Cassandra.
     - `powerbi_complaints_by_borough.csv` — distribución por distrito desde Cassandra.
     - `powerbi_complaints_by_type.csv` — tipos de quejas desde Cassandra.
     - `powerbi_complaints_by_status.csv` — estados de resolución desde Cassandra.
     - `powerbi_complaints_by_agency_day.csv` — actividad por agencia y fecha desde Cassandra.
     - `powerbi_mongo_sample.csv` — muestra de documentos originales desde MongoDB.
     - `powerbi_neo4j_nodes.csv` — nodos del grafo con grado de conexión desde Neo4j.
     - `powerbi_neo4j_relationships.csv` — relaciones entre entidades desde Neo4j.

---

## 🚀 Instrucciones de Ejecución

Sigue estos pasos en tu terminal para levantar el entorno y probar todas las funcionalidades:

### Paso 1: Configurar el Entorno Virtual de Python
Asegúrate de que tienes instalado Python 3.10+ y crea el entorno virtual local para instalar las dependencias:

```bash
# Crear el entorno virtual
python3 -m venv .venv

# Activar el entorno
source .venv/bin/activate

# Instalar dependencias globales del proyecto
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 2: Preparar permisos de la carpeta de datos

Antes de levantar Docker, asegúrate de que la carpeta `data/` tenga permisos de escritura para el usuario del contenedor Airflow (UID 50000). Si no se hace esto, el pipeline fallará con `PermissionError` al intentar escribir los archivos intermedios:

```bash
# Dar permisos de escritura a la carpeta de datos (necesario solo la primera vez)
chmod -R 777 data/
```

### Paso 3: Iniciar la Infraestructura Docker
Levanta los servicios de bases de datos y orquestación. Hemos limitado las memorias heap de Cassandra y Neo4j en `docker-compose.yml` para evitar cuellos de botella de memoria (OOM / exit 137).

```bash
# Levantar contenedores en segundo plano
docker compose up -d
```

Para verificar que todos los servicios estén activos y saludables (`healthy`), ejecuta:
```bash
docker compose ps
```

> **Tiempos de arranque esperados:**
> - MongoDB: ~10 segundos
> - Neo4j: ~20 segundos
> - Cassandra: hasta **60 segundos** (el más lento, ten paciencia)
> - Airflow webserver: ~50 segundos adicionales (inicializa la BD y crea el usuario `admin`)
> - Airflow scheduler: arranca **después** de que el webserver esté `healthy`

### Paso 3: Ejecutar y Validar el Pipeline ETL
Puedes ejecutar todo el flujo ETL de dos formas diferentes:

#### Opción A: Prueba de Ejecución Local (Recomendado para pruebas rápidas)
Hemos configurado un script en la raíz que ejecuta localmente las funciones de extracción, limpieza de datos, carga en MongoDB, Cassandra y Neo4j, y cálculo de KPIs.
```bash
# Con el entorno virtual activo (.venv)
python test_local_etl.py
```
El script mostrará logs del progreso de inserción en lotes y terminará imprimiendo un reporte de éxito.

#### Opción B: Ejecución desde Apache Airflow UI
Si prefieres ver la orquestación en la interfaz gráfica:
1. Abre en tu navegador: [http://localhost:8080](http://localhost:8080)
2. Inicia sesión con las credenciales por defecto:
   - **Usuario**: `admin`
   - **Contraseña**: `admin`
3. En la lista de DAGs, busca `nyc_311_etl_pipeline`. Si la lista aparece vacía, espera 30 segundos y recarga — el scheduler necesita parsear el archivo del DAG por primera vez.
4. Activa el DAG (switch On) y haz clic en **Trigger DAG** (icono de play) para iniciar la ejecución. Puedes inspeccionar las tareas en tiempo real desde la vista de grafo.

> **IMPORTANTE — No borres el DAG desde la UI:** Si accidentalmente haces clic en "Delete DAG", el archivo en disco sigue intacto. Para recuperarlo, espera 30 segundos y el scheduler lo volverá a registrar automáticamente, o ejecuta:
> ```bash
> docker exec nyc_311_airflow_scheduler airflow dags reserialize
> ```

### Paso 4: Ejecutar los Scripts de Demostración CRUD
Para demostrar operaciones de inserción, lectura, actualización y eliminación de prueba sobre cada base de datos, ejecuta los siguientes scripts en Python:

```bash
# CRUD sobre MongoDB (crea, consulta, actualiza y elimina el documento 'TEST001')
python db/mongodb/crud_demo.py

# CRUD sobre Cassandra (inserta, consulta, actualiza y elimina datos analíticos de 'TEST_BOROUGH')
python db/cassandra/crud_demo.py

# CRUD sobre Neo4j (crea un incidente y agencia, crea su relación, actualiza el estado y los elimina)
python db/neo4j/crud_demo.py
```

### Paso 5: Exportar Datos para Power BI
Con los contenedores Docker corriendo y los datos ya cargados (Paso 3), ejecuta el script de exportación:

```bash
# Genera todos los CSV en la carpeta exports/
python export_for_powerbi.py
```

El script se conecta a las 3 bases de datos y guarda los CSV en `./exports/`. Verás una salida similar a:
```
📦 Exportando desde Cassandra...
  ✅ powerbi_complaints_by_day.csv  (365 filas)
  ✅ powerbi_complaints_by_borough.csv  (6 filas)
  ...
📦 Exportando desde MongoDB...
  ✅ powerbi_mongo_sample.csv  (50,000 filas)
📦 Exportando desde Neo4j...
  ✅ powerbi_neo4j_nodes.csv  (X filas)
  ✅ powerbi_neo4j_relationships.csv  (X filas)
```

#### Cargar en Power BI Desktop:
1. Abre **Power BI Desktop**.
2. Selecciona **Obtener datos → Texto/CSV**.
3. Importa los archivos de la carpeta `exports/` uno por uno.
4. En el **Editor de Power Query** relaciona las tablas por campos comunes (`complaint_type`, `borough`, `agency`).
5. Diseña las visualizaciones y KPIs en el canvas.

---

## Resetear las Bases de Datos (Empezar desde Cero)

> **IMPORTANTE:** `docker compose down` **NO borra los datos**. Los datos persisten en volúmenes Docker nombrados aunque el contenedor esté apagado.

### Borrar TODO y empezar desde cero
```bash
# Apaga contenedores y elimina todos los volúmenes (Mongo + Cassandra + Neo4j + Airflow)
docker compose down -v
```

Luego vuelve a levantar normalmente:
```bash
chmod -R 777 data/
docker compose up -d
```

### Borrar solo una base de datos específica
Primero apaga los contenedores, luego borra el volumen que necesitas:
```bash
docker compose down

# Solo MongoDB
docker volume rm proyecto2-bigdata_mongo_data

# Solo Cassandra
docker volume rm proyecto2-bigdata_cassandra_data

# Solo Neo4j
docker volume rm proyecto2-bigdata_neo4j_data

# Solo historial de Airflow (runs y logs)
docker volume rm proyecto2-bigdata_airflow_home
```

### Referencia rápida

| Comando | Contenedores | Datos (Volúmenes) |
|---|---|---|
| `docker compose stop` | Pausados | Intactos |
| `docker compose down` | Eliminados | **Intactos** |
| `docker compose down -v` | Eliminados | **Eliminados** |
