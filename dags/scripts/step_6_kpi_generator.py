import json
import os
from collections import Counter
from datetime import datetime

def calculate_and_save_kpis(**kwargs):
    """
    Genera automáticamente los KPIs a partir de los datos procesados y guardados.
    """
    print("Iniciando la generación automática de indicadores (KPIs)...")
    
    input_path = '/opt/airflow/data/cleaned_data.json'
    if not os.path.exists(input_path):
        input_path = './data/cleaned_data.json'
        if not os.path.exists(input_path):
            print("[AVISO] No se encontró el dataset limpio. Cancelando KPIs.")
            return False
            
    with open(input_path, 'r', encoding='utf-8') as infile:
        records = json.load(infile)
        
    total_records = len(records)
    if total_records == 0:
        print("No hay registros para calcular KPIs.")
        return False

    dates = [r['created_date'].split('T')[0] for r in records if r['created_date']]
    incidents_by_day = Counter(dates)
    
    sorted_days = sorted(incidents_by_day.keys())
    daily_growth = {}
    for idx in range(1, len(sorted_days)):
        prev_day = sorted_days[idx - 1]
        curr_day = sorted_days[idx]
        growth = incidents_by_day[curr_day] - incidents_by_day[prev_day]
        daily_growth[f"{prev_day} -> {curr_day}"] = growth
        
    boroughs = [r['borough'] for r in records if r['borough']]
    boroughs_counter = Counter(boroughs)
    top_borough = boroughs_counter.most_common(1)[0] if boroughs_counter else ("N/A", 0)
    
    channels = [r['open_data_channel_type'] for r in records if r['open_data_channel_type']]
    channel_counter = Counter(channels)
    top_channel = channel_counter.most_common(1)[0] if channel_counter else ("N/A", 0)

    complaints = [r['complaint_type'] for r in records if r['complaint_type']]
    complaints_counter = Counter(complaints)
    top_5_complaints = complaints_counter.most_common(5)

    kpi_report = {
        "calculated_at": datetime.now().isoformat(),
        "total_records_processed": total_records,
        "kpi_1_records_by_day_sample": dict(list(incidents_by_day.items())[:5]),
        "kpi_2_growth_sample": dict(list(daily_growth.items())[:5]),
        "kpi_3_top_borough": {
            "borough": top_borough[0],
            "total_incidents": top_borough[1]
        },
        "kpi_4_top_report_channel": {
            "channel": top_channel[0],
            "total_reports": top_channel[1]
        },
        "kpi_5_top_complaints": [
            {"complaint_type": comp[0], "count": comp[1]} for comp in top_5_complaints
        ]
    }
    
    output_dir = os.path.dirname(input_path)
    output_kpi_path = os.path.join(output_dir, 'kpi_report.json')
    with open(output_kpi_path, 'w', encoding='utf-8') as outfile:
        json.dump(kpi_report, outfile, indent=2)
        
    print(f"KPIs calculados con éxito. Reporte guardado en {output_kpi_path}")
    print(f"Total registros: {total_records}")
    print(f"Barrio más afectado: {top_borough[0]} con {top_borough[1]} incidentes.")
    return True
