import requests
import os
import sys
from datetime import datetime
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import math

# Añadir el directorio raíz al sys.path para poder importar db_connections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection

# --- Configuración ---
API_BASE_URL = "https://service7.unap.edu.pe/api/v1/sunedu/consulta/{dni}"
API_TOKEN = "1|xrpNWzmI8EdDfvnKQpURERHiO4RraB4WmcIr810MjapBmmjXKWNGczJGTY"
MAX_CONCURRENT_REQUESTS = 15
BATCH_SIZE = 350              # Tamaño del lote ajustado a 350
DELAY_BETWEEN_BATCHES = 5     # Segundos de espera entre lotes

def fetch_sunedu_data(user_info):
    """Función concurrente para obtener datos de un DNI desde la API de SUNEDU."""
    user_id, dni = user_info
    try:
        headers = {'Authorization': f'Bearer {API_TOKEN}'}
        response = requests.get(API_BASE_URL.format(dni=dni), headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', {}).get('gtPersona', [])
            if data:
                for degree in data:
                    degree['user_id'] = user_id
                return data
        return None
    except requests.exceptions.RequestException as e:
        print(f"   - Error de red para DNI {dni}: {e}")
        return None

def extract_sunedu_data_to_csv_batched():
    """
    Script Extractor Mejorado:
    1. Lee DNIs de docentes desde PostgreSQL.
    2. Procesa las consultas a la API en lotes para respetar los límites.
    3. Guarda los resultados acumulados en dos archivos CSV.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        print("✅ Conectado a PostgreSQL para leer DNIs.")

        # 1. Obtener DNIs de todos los docentes con DNI válido
        cur.execute("""
            SELECT u.id, u.num_doc_identidad
            FROM tbl_usuarios u
            JOIN tbl_docentes d ON u.id = d.id_usuario
            WHERE LENGTH(TRIM(u.num_doc_identidad)) = 8
        """)
        users_to_process = cur.fetchall()
        total_users = len(users_to_process)
        
        if not users_to_process:
            print("👥 No se encontraron docentes con DNI válido para procesar.")
            return
        
        total_batches = math.ceil(total_users / BATCH_SIZE)
        print(f"👥 Encontrados {total_users} docentes. Se procesarán en {total_batches} lotes de hasta {BATCH_SIZE} cada uno.")

        # 2. Procesar en lotes
        all_degrees = []
        for i in range(total_batches):
            start_index = i * BATCH_SIZE
            end_index = start_index + BATCH_SIZE
            current_batch = users_to_process[start_index:end_index]
            
            print(f"\n--- 🚀 Procesando Lote {i+1}/{total_batches} ({len(current_batch)} usuarios) ---")

            with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
                future_to_user = {executor.submit(fetch_sunedu_data, user): user for user in current_batch}
                
                batch_results = []
                for j, future in enumerate(as_completed(future_to_user)):
                    print(f"   Procesando respuesta {j+1}/{len(current_batch)}...", end='\r')
                    result = future.result()
                    if result:
                        batch_results.extend(result)
            
            all_degrees.extend(batch_results)
            print(f"\n   ✅ Lote {i+1} completado. {len(batch_results)} grados encontrados en este lote.")
            
            if i < total_batches - 1:
                print(f"   ⏳ Esperando {DELAY_BETWEEN_BATCHES} segundos antes del siguiente lote...")
                time.sleep(DELAY_BETWEEN_BATCHES)

        print(f"\n✅ Procesamiento de todos los lotes completado. Se encontraron un total de {len(all_degrees)} registros de grados.")

        if not all_degrees:
            print("No se encontraron grados en total. No se generarán archivos CSV.")
            return

        # 3. Procesar datos acumulados y generar CSVs una sola vez al final
        output_dir = os.path.join(os.path.dirname(__file__), '..')
        uni_csv_path = os.path.join(output_dir, 'dic_universidades_export.csv')
        estudios_csv_path = os.path.join(output_dir, 'tbl_estudios_export.csv')

        universidades = {
            degree.get('universidad'): {
                "abreviatura": degree.get('siglas', ''),
                "pais": degree.get('pais', 'PER'),
                "tipo_institucion": degree.get('tipoInstitucion', 'U'),
                "tipo_gestion": degree.get('tipoGestion', 'P')
            }
            for degree in all_degrees if degree.get('universidad')
        }
        
        print(f"🏫 Se encontraron {len(universidades)} universidades únicas. Guardando en {uni_csv_path}")
        with open(uni_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['nombre', 'abreviatura', 'estado_dic_universidades', 'pais', 'tipo_institucion', 'tipo_gestion'])
            for name, attrs in universidades.items():
                writer.writerow([name, attrs['abreviatura'], 1, attrs['pais'], attrs['tipo_institucion'], attrs['tipo_gestion']])

        print(f"🎓 Se procesarán {len(all_degrees)} registros de estudios. Guardando en {estudios_csv_path}")
        with open(estudios_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id_usuario', 'universidad_nombre', 'grado_abreviatura', 'titulo_profesional',
                'especialidad', 'fecha_emision', 'resolucion',
                'fecha_resolucion', 'flag_resolucion_nulidad', 'nro_resolucion_nulidad', 
                'fecha_resolucion_nulidad', 'tipo_obtencion_nombre'
            ])
            for degree in all_degrees:
                try:
                    fecha_emision = datetime.strptime(degree.get('fechaEmision'), '%d/%m/%Y').strftime('%Y-%m-%d') if degree.get('fechaEmision') else ''
                except (ValueError, TypeError):
                    fecha_emision = ''
                
                writer.writerow([
                    degree.get('user_id'), degree.get('universidad'), degree.get('abreviaturaTitulo'),
                    degree.get('tituloProfesional'), degree.get('especialidad'), fecha_emision,
                    degree.get('resolucion'), '', '', '', '', 'API SUNEDU'
                ])
        
        print("\n🎉 Proceso de extracción a CSV finalizado exitosamente!")

    except Exception as e:
        print(f"❌ Error crítico durante el proceso de extracción: {e}")
    finally:
        if conn:
            conn.close()
            print("🔌 Conexión a PostgreSQL cerrada.")

if __name__ == "__main__":
    extract_sunedu_data_to_csv_batched()