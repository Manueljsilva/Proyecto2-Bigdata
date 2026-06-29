// Crear restricciones de unicidad (Node Keys)
CREATE CONSTRAINT unique_key_ServiceRequest_key IF NOT EXISTS
FOR (n:ServiceRequest)
REQUIRE n.unique_key IS UNIQUE;

CREATE CONSTRAINT agency_Agency_key IF NOT EXISTS
FOR (n:Agency)
REQUIRE n.agency IS UNIQUE;

CREATE CONSTRAINT complaint_type_ComplaintType_key IF NOT EXISTS
FOR (n:ComplaintType)
REQUIRE n.complaint_type IS UNIQUE;

CREATE CONSTRAINT descriptor_id_Descriptor_key IF NOT EXISTS
FOR (n:Descriptor)
REQUIRE n.descriptor_id IS UNIQUE;

CREATE CONSTRAINT borough_Borough_key IF NOT EXISTS
FOR (n:Borough)
REQUIRE n.borough IS UNIQUE;

CREATE CONSTRAINT open_data_channel_type_Channel_key IF NOT EXISTS
FOR (n:Channel)
REQUIRE n.open_data_channel_type IS UNIQUE;
