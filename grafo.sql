-- crear nodos
-- Crear nodos ServiceRequest
CREATE CONSTRAINT `unique_key_ServiceRequest_key` IF NOT EXISTS
FOR (n: `ServiceRequest`)
REQUIRE (n.`unique_key`) IS NODE KEY;

-- Crear nodos Agency
CREATE CONSTRAINT `agency_Agency_key` IF NOT EXISTS
FOR (n: `Agency`)
REQUIRE (n.`agency`) IS NODE KEY;

-- Crear nodos ComplaintType
CREATE CONSTRAINT `complaint_type_ComplaintType_key` IF NOT EXISTS
FOR (n: `ComplaintType`)
REQUIRE (n.`complaint_type`) IS NODE KEY;

-- Crear nodos Descriptor
CREATE CONSTRAINT `descriptor_id_Descriptor_key` IF NOT EXISTS
FOR (n: `Descriptor`)
REQUIRE (n.`descriptor_id`) IS NODE KEY;

-- Crear nodos Borough
CREATE CONSTRAINT `borough_Borough_key` IF NOT EXISTS
FOR (n: `Borough`)
REQUIRE (n.`borough`) IS NODE KEY;

-- Crear nodos Channel
CREATE CONSTRAINT `open_data_channel_type_Channel_key` IF NOT EXISTS
FOR (n: `Channel`)
REQUIRE (n.`open_data_channel_type`) IS NODE KEY;



-- Crear relaciones del grafo

-- Relación HANDLED_BY
UNWIND $relRecords AS relRecord
MATCH (source: `ServiceRequest` { `unique_key`: toInteger(trim(relRecord.`unique_key`)) })
MATCH (target: `Agency` { `agency`: relRecord.`agency` })
MERGE (source)-[r: `HANDLED_BY`]->(target);

-- Relación HAS_COMPLAINT_TYPE
UNWIND $relRecords AS relRecord
MATCH (source: `ServiceRequest` { `unique_key`: toInteger(trim(relRecord.`unique_key`)) })
MATCH (target: `ComplaintType` { `complaint_type`: relRecord.`location_type` })
MERGE (source)-[r: `HAS_COMPLAINT_TYPE`]->(target);

-- Relación HAS_DESCRIPTOR
UNWIND $relRecords AS relRecord
MATCH (source: `ServiceRequest` { `unique_key`: toInteger(trim(relRecord.`unique_key`)) })
MATCH (target: `Descriptor` { `descriptor_id`: relRecord.`descriptor_id` })
MERGE (source)-[r: `HAS_DESCRIPTOR`]->(target);

-- Relación OCCURRED_IN_BOROUGH
UNWIND $relRecords AS relRecord
MATCH (source: `ServiceRequest` { `unique_key`: toInteger(trim(relRecord.`unique_key`)) })
MATCH (target: `Borough` { `borough`: relRecord.`borough` })
MERGE (source)-[r: `OCCURRED_IN_BOROUGH`]->(target);

-- Relación REPORTED_THROUGH
UNWIND $relRecords AS relRecord
MATCH (source: `ServiceRequest` { `unique_key`: toInteger(trim(relRecord.`unique_key`)) })
MATCH (target: `Channel` { `open_data_channel_type`: relRecord.`open_data_channel_type` })
MERGE (source)-[r: `REPORTED_THROUGHs`]->(target)
SET r.`unique_key` = toInteger(trim(relRecord.`unique_key`))
SET r.`open_data_channel_type` = relRecord.`open_data_channel_type`;

-- Relación BELONGS_TO_TYPE
UNWIND $relRecords AS relRecord
MATCH (source: `Descriptor` { `descriptor_id`: relRecord.`descriptor_id` })
MATCH (target: `ComplaintType` { `complaint_type`: relRecord.`complaint_type` })
MERGE (source)-[r: `BELONGS_TO_TYPE`]->(target);

-- ALGUNAS CONSULTAS

-- Tipos de reclamo más frecuentes 
MATCH (r:ServiceRequest)-[:HAS_COMPLAINT_TYPE]->(ct:ComplaintType)
RETURN ct.complaint_type AS tipo_reclamo,
       count(r) AS total_solicitudes
ORDER BY total_solicitudes DESC
LIMIT 10;


-- Boroughs con mayor cantidad de solicitudes 

MATCH (r:ServiceRequest)-[:OCCURRED_IN_BOROUGH]->(b:Borough)
RETURN b.borough AS borough,
       count(r) AS total_solicitudes
ORDER BY total_solicitudes DESC;

-- Entidades con mayor número de conexiones 
MATCH (n)
RETURN labels(n) AS tipo_nodo,
       coalesce(n.agency, n.complaint_type, n.descriptor, n.borough, n.open_data_channel_type, n.unique_key) AS entidad,
       count { (n)--() } AS grado_conexion
ORDER BY grado_conexion DESC
LIMIT 20;
