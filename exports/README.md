# 📊 Carpeta de Exportación para Power BI

Esta carpeta contiene los archivos CSV generados automáticamente por el pipeline ETL
(o manualmente con `export_for_powerbi.py`) para ser consumidos por **Power BI Desktop**.

## Archivos Generados

| Archivo | Fuente | Descripción |
|---|---|---|
| `powerbi_complaints_by_day.csv` | Cassandra | Volumen de quejas por fecha |
| `powerbi_complaints_by_borough.csv` | Cassandra | Quejas por distrito (Borough) |
| `powerbi_complaints_by_type.csv` | Cassandra | Quejas por tipo de incidente |
| `powerbi_complaints_by_status.csv` | Cassandra | Estado de resolución de quejas |
| `powerbi_complaints_by_agency_day.csv` | Cassandra | Quejas por agencia y fecha |
| `powerbi_mongo_sample.csv` | MongoDB | Muestra de documentos originales |
| `powerbi_neo4j_nodes.csv` | Neo4j | Nodos del grafo con tipo y nombre |
| `powerbi_neo4j_relationships.csv` | Neo4j | Relaciones entre entidades del grafo |

## Cómo Usar en Power BI

1. Abre **Power BI Desktop**
2. Selecciona **Obtener datos → Texto/CSV**
3. Importa los archivos de esta carpeta
4. En el **Editor de Power Query** puedes cruzar las tablas por `complaint_type`, `borough`, `agency`, etc.
5. Crea las visualizaciones y KPIs en el canvas

## Cómo Regenerar los CSV

```bash
# Con los contenedores Docker corriendo:
python export_for_powerbi.py

# El script se conecta a las 3 bases de datos y sobreescribe los CSV de esta carpeta.
```
