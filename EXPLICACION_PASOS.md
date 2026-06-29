# Explicación Detallada de los Pasos y Cumplimiento de Requisitos

Este documento sirve como un desglose técnico del pipeline ETL, los CRUDs y el Dashboard implementados para el proyecto **NYC 311 Service Requests**, bajo el patrón de diseño **Landing Zone (Ingesta Incremental)**.

---

## Resumen del Cumplimiento de Requisitos

| Requisito del PDF | Estado | Implementación |
| :--- | :---: | :--- |
| **Fuente de Datos** (Manejo incremental) | **CUMPLIDO** | Ingesta por carpetas (Landing Zone). Los archivos nuevos en `data/raw/` se procesan y se archivan en `data/processed/`. |
| **MongoDB** (Carga incremental y Source of Truth) | **CUMPLIDO** | Colección `complaints_raw` guarda el histórico acumulado. Omite claves duplicadas de forma segura y veloz usando `ordered=False`. |
| **Cassandra** (Series temporales actualizadas) | **CUMPLIDO** | Sincronización analítica directa desde MongoDB: recalcula agregados globales mediante queries agregadas nativas de MongoDB y los escribe limpios en Cassandra. |
| **Neo4j** (Modelar relaciones del grafo) | **CUMPLIDO** | Creación de 6 constraints de clave y carga incremental de nuevas quejas mediante Cypher `MERGE`. |
| **Automatización con Airflow** (Flujo programado) | **CUMPLIDO** | DAG `nyc_311_etl_pipeline` con 6 tareas secuenciadas y en paralelo con manejo de salud en Docker. |
| **Operaciones CRUD** (Crear, Leer, Actualizar, Eliminar) | **CUMPLIDO** | Tres scripts Python interactivos e independientes para MongoDB, Cassandra y Neo4j. |
| **Dashboard Analítico** (Power BI) | **CUMPLIDO** | Exportación de datos de las 3 BDs a CSV mediante `export_for_powerbi.py`. Los archivos en `exports/` se importan en Power BI Desktop para construir las visualizaciones e indicadores. |

---

## Detalle Paso a Paso del Pipeline ETL (Incremental)

### Paso 1: Extracción (`step_1_extractor.py`)
* **Qué hace exactamente**: 
  - Escanea el directorio de entrada `data/raw/` buscando **cualquier** archivo con extensión `.jsonl`.
  - Si la carpeta está vacía, guarda un archivo temporal vacío y termina de forma segura, permitiendo ejecuciones programadas exitosas sin datos nuevos.
  - Si encuentra archivos, lee línea por línea combinando los registros de todos los archivos y los consolida en `extracted_raw.json`.
  - **Archivado**: Mueve los archivos procesados a la carpeta `data/processed/`, renombrándolos con un prefijo de marca de tiempo (ej. `20260628_131610_archivo.jsonl`) para vaciar la landing zone y mantener un histórico inmutable.
* **Cómo cumple con lo pedido**: Implementa una verdadera zona de aterrizaje ("Landing Zone") que simula la recepción periódica de nuevos registros por lotes.

### Paso 2: Validación y Limpieza (`step_2_cleaner.py`)
* **Qué hace exactamente**:
  - Asegura tipos de datos correctos (claves como string, coordenadas de geolocalización como float, etc.).
  - Estandariza fechas a formato ISO-8601 (`YYYY-MM-DDTHH:MM:SS`).
  - Convierte ciudades y distritos a mayúsculas homogéneas.
  - **Deduplicación**: Implementa un filtro que elimina registros repetidos por `unique_key` garantizando la calidad de los datos del lote.
* **Cómo cumple con lo pedido**: Proceso de **Validación y limpieza**. Al filtrar duplicados y validar tipos antes de la carga, evita caídas por colisiones de claves en los gestores de bases de datos.

### Paso 3: Carga Incremental en MongoDB (`step_3_mongo_loader.py`)
* **Qué hace exactamente**:
  - Conecta a MongoDB mediante `pymongo`.
  - Asegura los 6 índices analíticos sobre la colección `complaints_raw`.
  - Inserta los nuevos registros en lotes de 5,000 utilizando `ordered=False`. Esto permite a MongoDB omitir silenciosamente colisiones de claves duplicadas (código de error `11000`) si una queja ya había sido cargada en el pasado, permitiendo insertar sin problemas el resto de las quejas nuevas.
* **Cómo cumple con lo pedido**: Etapa de **Carga en MongoDB**. Actúa como nuestro **lago de datos operacional / única fuente de verdad** (Single Source of Truth), acumulando el histórico total.

### Paso 4: Sincronización Analítica en Cassandra (`step_4_cassandra_loader.py`)
* **Qué hace exactamente**:
  - Para evitar que las métricas de Cassandra queden incompletas (ya que cada ejecución de Airflow procesa lotes independientes), este script se conecta a MongoDB y ejecuta **5 pipelines de agregación nativa** sobre toda la colección histórica de quejas.
  - Esto recalcula el total de quejas globales por día, por distrito, por tipo, por estado y por agencia-día.
  - Trunca (vacía) las 5 tablas analíticas en Cassandra y recarga instantáneamente los totales históricos actualizados usando prepared statements del driver de Cassandra.
* **Cómo cumple con lo pedido**: Etapa de **Transformación y carga en Cassandra**. Utiliza Cassandra para almacenar resúmenes analíticos indexados de alta velocidad, garantizando que el Dashboard siempre muestre estadísticas globales correctas aunque los datos ingresen de forma fraccionada.

### Paso 5: Construcción Incremental del Grafo en Neo4j (`step_5_neo4j_loader.py`)
* **Qué hace exactamente**:
  - Conecta a Neo4j mediante el protocolo `bolt`.
  - Asegura las 6 restricciones de unicidad de clave.
  - Sin borrar el grafo anterior, procesa el lote actual usando la sentencia Cypher **`MERGE`** en transacciones rápidas de 2,000 registros. Si una entidad (como una Agencia o Distrito) ya existe, la reutiliza; si es un caso nuevo, lo crea y lo enlaza en la red de grafos.
* **Cómo cumple con lo pedido**: Etapa de **Construcción de relaciones y carga en Neo4j**. Permite que la red de grafos crezca de forma acumulativa y relacione casos nuevos con entidades ya conocidas.

### Paso 6: Generación Automática de Indicadores (`step_6_kpi_generator.py`)
* **Qué hace exactamente**:
  - Lee el archivo de datos limpios del lote actual (`cleaned_data.json`).
  - Calcula los 5 KPIs definidos para el proyecto utilizando contadores en memoria:
    - **KPI 1**: Total de registros procesados por día (distribución temporal).
    - **KPI 2**: Crecimiento diario de eventos (diferencia entre días consecutivos).
    - **KPI 3**: Distrito (Borough) con mayor número de incidentes reportados.
    - **KPI 4**: Canal de reporte más utilizado por los ciudadanos.
    - **KPI 5**: Top 5 tipos de quejas más frecuentes.
  - Guarda el resultado como `data/kpi_report.json` con marca de tiempo del cálculo.
* **Cómo cumple con lo pedido**: Etapa de **Generación automática de indicadores**. Produce un reporte JSON auditable en cada ejecución del DAG, garantizando trazabilidad de métricas por lote.

---

## Exportación para Power BI (`export_for_powerbi.py`)

Este script se ejecuta de forma **independiente al DAG** (no es parte del pipeline automático) y sirve para alimentar el dashboard de Power BI.

* **Qué hace exactamente**:
  - Se conecta a las 3 bases de datos simultáneamente (MongoDB, Cassandra y Neo4j).
  - Exporta los datos procesados y agregados a archivos CSV en la carpeta `exports/`:
    - `powerbi_complaints_by_day.csv` — serie temporal desde Cassandra.
    - `powerbi_complaints_by_borough.csv` — distribución por distrito desde Cassandra.
    - `powerbi_complaints_by_type.csv` — tipos de quejas desde Cassandra.
    - `powerbi_complaints_by_status.csv` — estados de resolución desde Cassandra.
    - `powerbi_complaints_by_agency_day.csv` — actividad por agencia y fecha desde Cassandra.
    - `powerbi_mongo_sample.csv` — hasta 50,000 documentos originales desde MongoDB.
    - `powerbi_neo4j_nodes.csv` — nodos del grafo con su grado de conexión desde Neo4j.
    - `powerbi_neo4j_relationships.csv` — relaciones entre entidades del grafo desde Neo4j.
* **Cómo se usa**: Con los contenedores Docker corriendo y los datos ya cargados, ejecutar `python export_for_powerbi.py`. Los CSV generados se importan directamente en Power BI Desktop para construir el dashboard analítico.
