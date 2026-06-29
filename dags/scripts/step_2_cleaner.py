import json
import os
from datetime import datetime

def clean_extracted_data(input_path, output_path, **kwargs):

    print(f"Iniciando validación y limpieza desde: {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró el archivo temporal en {input_path}")
        
    with open(input_path, 'r', encoding='utf-8') as infile:
        data = json.load(infile)
        
    cleaned_records = []
    seen_keys = set()
    
    for record in data:
        unique_key = record.get("unique_key")
        if not unique_key:
            continue
            
        unique_key_str = str(unique_key).strip()
        if unique_key_str in seen_keys:
            continue
        seen_keys.add(unique_key_str)
            
        created_date_raw = record.get("created_date")
        created_date = None
        if created_date_raw:
            try:
                clean_date_str = created_date_raw.replace('T', ' ')
                if '.' in clean_date_str:
                    clean_date_str = clean_date_str.split('.')[0]
                created_date = datetime.strptime(clean_date_str, "%Y-%m-%d %H:%M:%S").isoformat()
            except Exception:
                created_date = None

        closed_date_raw = record.get("closed_date")
        closed_date = None
        if closed_date_raw and closed_date_raw != "N/A":
            try:
                clean_date_str = closed_date_raw.replace('T', ' ')
                if '.' in clean_date_str:
                    clean_date_str = clean_date_str.split('.')[0]
                closed_date = datetime.strptime(clean_date_str, "%Y-%m-%d %H:%M:%S").isoformat()
            except Exception:
                closed_date = None

        latitude = record.get("latitude")
        longitude = record.get("longitude")
        
        try:
            latitude = float(latitude) if latitude and latitude != "N/A" else None
        except ValueError:
            latitude = None
            
        try:
            longitude = float(longitude) if longitude and longitude != "N/A" else None
        except ValueError:
            longitude = None

        if (latitude is None or longitude is None) and "location" in record:
            loc = record["location"]
            if isinstance(loc, dict) and loc.get("type") == "Point":
                coords = loc.get("coordinates")
                if isinstance(coords, list) and len(coords) == 2:
                    longitude = float(coords[0])
                    latitude = float(coords[1])

        borough = record.get("borough", "UNSPECIFIED").strip().upper()
        agency = record.get("agency", "UNSPECIFIED").strip().upper()
        complaint_type = record.get("complaint_type", "UNSPECIFIED").strip()
        descriptor = record.get("descriptor", "N/A").strip()

        cleaned_record = {
            "unique_key": str(unique_key),
            "created_date": created_date,
            "closed_date": closed_date,
            "agency": agency,
            "agency_name": record.get("agency_name", "Unspecified Agency"),
            "complaint_type": complaint_type,
            "descriptor": descriptor,
            "status": record.get("status", "Open"),
            "incident_zip": record.get("incident_zip", "00000"),
            "incident_address": record.get("incident_address", "N/A"),
            "city": record.get("city", "UNSPECIFIED").strip().upper(),
            "borough": borough,
            "latitude": latitude,
            "longitude": longitude,
            "open_data_channel_type": record.get("open_data_channel_type", "UNKNOWN")
        }
        
        cleaned_records.append(cleaned_record)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(cleaned_records, outfile, indent=2)
        
    print(f"Limpieza completada. Registros válidos guardados: {len(cleaned_records)}")
    return len(cleaned_records)
