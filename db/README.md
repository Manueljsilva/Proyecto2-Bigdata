# Scripts de Bases de Datos y Operaciones CRUD

Esta carpeta está organizada por cada base de datos utilizada en el proyecto. 

## Estructura
Cada subcarpeta (`mongodb`, `cassandra`, `neo4j`) debe contener:
1. El script de inicialización o definición del esquema (`schema.*`).
2. Un script demostrativo de operaciones CRUD (`crud_demo.py`) como requiere el proyecto:
   - **MongoDB:** Crear, consultar, actualizar y eliminar un documento.
   - **Cassandra:** Inserción, consulta, actualización y eliminación.
   - **Neo4j:** Crear nodo, crear relación, actualizar propiedades y eliminar nodo/relación.
