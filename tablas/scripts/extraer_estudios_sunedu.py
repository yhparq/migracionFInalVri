import requests
import os
import sys
from datetime import datetime
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import math

# Añadir el directorio raíz del proyecto al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection

# --- Configuración ---
API_BASE_URL = "https://service7.unap.edu.pe/api/v1/sunedu/consulta/{dni}"
API_TOKEN = "1|xrpNWzmI8EdDfvnKQpURERHiO4RraB4WmcIr810MjapBmmjXKWNGczJGTY"
MAX_CONCURRENT_REQUESTS = 15
BATCH_SIZE = 200 # Tamaño de lote ajustado a 200
DELAY_BETWEEN_BATCHES = 2 # Pausa más corta entre lotes

def fetch_sunedu_data(user_info):
    """Función concurrente para obtener datos de un DNI desde la API de SUNEDU."""
    user_id, dni = user_info
    try:
        headers = {'Authorization': f'Bearer {API_TOKEN}'}
        response = requests.get(API_BASE_URL.format(dni=dni), headers=headers, timeout=20) # Timeout aumentado
        if response.status_code == 200:
            data = response.json().get('data', {}).get('gtPersona', [])
            if data:
                for degree in data:
                    if isinstance(degree, dict):
                        degree['user_id'] = user_id
                return data
        return None
    except requests.exceptions.RequestException:
        return None

def append_to_csv(file_path, fieldnames, data_rows, is_first_batch):
    """Añade filas a un archivo CSV. Escribe el encabezado si es el primer lote."""
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if is_first_batch and not file_exists:
            writer.writeheader()
        writer.writerows(data_rows)

def extract_estudios_sunedu_to_csv_incremental():
    """
    Extrae los grados académicos desde la API, procesando en lotes y guardando
    el progreso en archivos CSV después de cada lote.
    """
    print("--- Iniciando extracción incremental de SUNEDU a CSV ---")
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        print("✅ Conectado a PostgreSQL para leer DNIs.")

        # 1. Limpiar archivos CSV antiguos al inicio de una nueva ejecución completa
        output_dir = os.path.dirname(__file__)
        uni_csv_path = os.path.join(output_dir, 'dic_universidades_extraido.csv')
        estudios_csv_path = os.path.join(output_dir, 'tbl_estudios_extraido.csv')
        if os.path.exists(uni_csv_path): os.remove(uni_csv_path)
        if os.path.exists(estudios_csv_path): os.remove(estudios_csv_path)
        print("🧹 Archivos CSV antiguos eliminados.")

        # 2. Obtener todos los DNIs de usuarios con formato válido
        cur.execute("SELECT id, num_doc_identidad FROM tbl_usuarios WHERE num_doc_identidad ~ '^[0-9]{8}$'")
        users_to_process = cur.fetchall()
        total_users = len(users_to_process)
        
        if not users_to_process:
            print("👥 No se encontraron usuarios con DNI válido para procesar.")
            return
        
        total_batches = math.ceil(total_users / BATCH_SIZE)
        print(f"👥 Encontrados {total_users} usuarios. Se procesarán en {total_batches} lotes de {BATCH_SIZE} cada uno.")

        universidades_procesadas_global = set()

        # 3. Procesar en lotes
        for i in range(total_batches):
            start_index = i * BATCH_SIZE
            end_index = start_index + BATCH_SIZE
            current_batch = users_to_process[start_index:end_index]
            
            print(f"\n--- 🚀 Procesando Lote {i+1}/{total_batches} ({len(current_batch)} usuarios) ---")
            
            batch_degrees = []
            with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
                future_to_user = {executor.submit(fetch_sunedu_data, user): user for user in current_batch}
                for j, future in enumerate(as_completed(future_to_user)):
                    print(f"   Procesando respuesta {j+1}/{len(current_batch)}...", end='\r')
                    result = future.result()
                    if result:
                        batch_degrees.extend(result)
            
            print(f"\n   ✅ Lote {i+1} completado. Se encontraron {len(batch_degrees)} grados.")

            # 4. Procesar y escribir los resultados del lote actual en los CSV
            if batch_degrees:
                universidades_lote = []
                estudios_lote = []

                for degree in batch_degrees:
                    if not isinstance(degree, dict): continue
                    
                    uni_name = degree.get('universidad')
                    if uni_name and uni_name not in universidades_procesadas_global:
                        universidades_procesadas_global.add(uni_name)
                        universidades_lote.append({
                            'nombre': uni_name, 'pais': degree.get('pais'),
                            'tipo_institucion': degree.get('tipoInstitucion'),
                            'tipo_gestion': degree.get('tipoGestion'), 'estado_dic_universidades': 1
                        })

                    try:
                        fecha_emision = datetime.strptime(degree.get('fechaEmision'), '%d/%m/%Y').strftime('%Y-%m-%d') if degree.get('fechaEmision') else None
                    except (ValueError, TypeError):
                        fecha_emision = None

                    estudios_lote.append({
                        'id_usuario': degree.get('user_id'), 'universidad_nombre': uni_name,
                        'grado_abreviatura': degree.get('abreviaturaTitulo'),
                        'titulo_profesional': degree.get('tituloProfesional'),
                        'especialidad': degree.get('especialidad'), 'fecha_emision': fecha_emision,
                        'resolucion': degree.get('resolucion'), 'tipo_obtencion_nombre': 'API SUNEDU'
                    })

                if universidades_lote:
                    append_to_csv(uni_csv_path, fieldnames=universidades_lote[0].keys(), data_rows=universidades_lote, is_first_batch=(i==0))
                    print(f"   ✍️  {len(universidades_lote)} nuevas universidades guardadas en CSV.")
                
                if estudios_lote:
                    append_to_csv(estudios_csv_path, fieldnames=estudios_lote[0].keys(), data_rows=estudios_lote, is_first_batch=(i==0))
                    print(f"   ✍️  {len(estudios_lote)} registros de estudios guardados en CSV.")

            if i < total_batches - 1:
                print(f"   ⏳ Esperando {DELAY_BETWEEN_BATCHES} segundos...")
                time.sleep(DELAY_BETWEEN_BATCHES)

        print("\n🎉 Proceso de extracción a CSV completado exitosamente!")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
    finally:
        if conn:
            conn.close()
            print("🔌 Conexión a PostgreSQL cerrada.")

if __name__ == "__main__":
    extract_estudios_sunedu_to_csv_incremental()