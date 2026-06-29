-- Crear el Keyspace
CREATE KEYSPACE IF NOT EXISTS nyc311_ks
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

USE nyc311_ks;

-- Tabla 1: Volumen de quejas por día
CREATE TABLE IF NOT EXISTS complaints_by_day (
  complaint_date date PRIMARY KEY,
  total int
);

-- Tabla 2: Volumen de quejas por distrito (Borough)
CREATE TABLE IF NOT EXISTS complaints_by_borough (
  borough text PRIMARY KEY,
  total int
);

-- Tabla 3: Volumen de quejas por tipo de queja
CREATE TABLE IF NOT EXISTS complaints_by_type (
  complaint_type text PRIMARY KEY,
  total int
);

-- Tabla 4: Volumen de quejas por estado de resolución
CREATE TABLE IF NOT EXISTS complaints_by_status (
  status text PRIMARY KEY,
  total int
);

-- Tabla 5: Volumen de quejas por agencia y día (ordenado por fecha desc)
CREATE TABLE IF NOT EXISTS complaints_by_agency_day (
  agency text,
  complaint_date date,
  total int,
  PRIMARY KEY (agency, complaint_date)
) WITH CLUSTERING ORDER BY (complaint_date DESC);
