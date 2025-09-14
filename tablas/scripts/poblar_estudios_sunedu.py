import requests
import os
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import math

# Añadir el directorio raíz al sys.path para poder importar db_connections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection

# --- Configuración ---
API_BASE_URL = "https://service7.unap.edu.pe/api/v1/sunedu/consulta/{dni}"
API_TOKEN = "1|xrpNWzmI8EdDfvnKQpURERHiO4RraB4WmcIr810MjapBmmjXKWNGczJGTY"
MAX_CONCURRENT_REQUESTS = 10  # Reducido para ser más cuidadoso con el API
MAX_QUERIES = 800             # Límite de seguridad para no exceder 1000 consultas
BATCH_SIZE = 200              # Tamaño del lote para procesamiento
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
                processed_data = []
                for degree in data:
                    # CORRECCIÓN: Asegurarse de que el registro es un diccionario antes de procesarlo
                    if isinstance(degree, dict):
                        degree['user_id'] = user_id
                        processed_data.append(degree)
                return processed_data if processed_data else None
        return None
    except requests.exceptions.RequestException as e:
        print(f"   - Error de red para DNI {dni}: {e}")
        return None

def get_or_create_university(cursor, uni_name, uni_details, cache):
    """Busca una universidad por nombre, si no existe, la crea y devuelve el ID."""
    if uni_name in cache:
        return cache[uni_name]
    
    cursor.execute("SELECT id FROM dic_universidades WHERE nombre = %s", (uni_name,))
    result = cursor.fetchone()
    if result:
        uni_id = result[0]
        cache[uni_name] = uni_id
        return uni_id
    else:
        print(f"      -> Nueva Universidad: '{uni_name}'. Insertando...")
        cursor.execute(
            """
            INSERT INTO dic_universidades (nombre, abreviatura, pais, tipo_institucion, tipo_gestion, estado_dic_universidades)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
            """,
            (
                uni_name,
                uni_details.get('siglas', ''),
                uni_details.get('pais', 'PER'),
                uni_details.get('tipoInstitucion', 'U'),
                uni_details.get('tipoGestion', 'P'),
                1  # CORREGIDO: Se envía 1 en lugar de True
            )
        )
        uni_id = cursor.fetchone()[0]
        cache[uni_name] = uni_id
        return uni_id

def populate_sunedu_data_directly():
    """
    Script Mejorado para Poblar Datos de SUNEDU Directamente:
    1.  Se conecta a PostgreSQL y carga diccionarios en memoria.
    2.  Obtiene una lista de DOCENTES con DNI válido, respetando el MAX_QUERIES.
    3.  Consulta el API de SUNEDU de forma concurrente y por lotes.
    4.  Para cada resultado:
        a. Busca o crea la universidad para obtener su ID.
        b. Mapea los nombres de grados y tipo de obtención a sus IDs.
        c. Inserta el registro directamente en la tabla `tbl_estudios`.
    5.  Maneja transacciones para garantizar la integridad de los datos.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()
        print("✅ Conectado a PostgreSQL.")

        # 1. Pre-cargar diccionarios de la DB para mapeo rápido
        cur.execute("SELECT abreviatura, id FROM dic_grados_academicos")
        grados_map = {row[0]: row[1] for row in cur.fetchall()}
        
        cur.execute("SELECT nombre, id FROM dic_obtencion_studios")
        obtencion_map = {row[0]: row[1] for row in cur.fetchall()}
        
        print(f"📚 Pre-cargados {len(grados_map)} grados académicos y {len(obtencion_map)} tipos de obtención.")

        # 2. Obtener DNIs de DOCENTES, aplicando el límite de consultas
        cur.execute("""
            SELECT u.id, u.num_doc_identidad
            FROM tbl_usuarios u
            JOIN tbl_docentes d ON u.id = d.id_usuario
            WHERE LENGTH(TRIM(u.num_doc_identidad)) = 8
            LIMIT %s
        """, (MAX_QUERIES,))
        users_to_process = cur.fetchall()
        
        if not users_to_process:
            print("👥 No se encontraron docentes con DNI válido para procesar.")
            return
        
        total_users = len(users_to_process)
        total_batches = math.ceil(total_users / BATCH_SIZE)
        print(f"👥 Encontrados {total_users} docentes. Se procesarán en {total_batches} lotes.")

        university_cache = {}
        total_degrees_found = 0
        total_degrees_inserted = 0

        # 3. Procesar en lotes
        for i in range(total_batches):
            start_index = i * BATCH_SIZE
            end_index = start_index + BATCH_SIZE
            current_batch = users_to_process[start_index:end_index]
            
            print(f"\n--- 🚀 Procesando Lote {i+1}/{total_batches} ({len(current_batch)} usuarios) ---")

            with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
                future_to_user = {executor.submit(fetch_sunedu_data, user): user for user in current_batch}
                
                for j, future in enumerate(as_completed(future_to_user)):
                    print(f"   Procesando respuesta {j+1}/{len(current_batch)}...", end='\r')
                    degrees = future.result()
                    
                    if not degrees:
                        continue
                    
                    total_degrees_found += len(degrees)
                    
                    # 4. Insertar los grados para este usuario en una transacción
                    try:
                        for degree in degrees:
                            uni_name = degree.get('universidad')
                            if not uni_name:
                                continue

                            # Obtener ID de la universidad (creándola si es necesario)
                            uni_id = get_or_create_university(cur, uni_name, degree, university_cache)

                            # Mapear IDs de grado y tipo de obtención
                            grado_abbr = degree.get('abreviaturaTitulo')
                            if grado_abbr not in grados_map:
                                print(f"      ⚠️ Omitiendo grado: Abreviatura desconocida '{grado_abbr}'")
                                continue
                            
                            id_grado_academico = grados_map[grado_abbr]
                            id_tipo_obtencion = obtencion_map.get('API SUNEDU')

                            # Formatear fecha
                            try:
                                fecha_emision = datetime.strptime(degree.get('fechaEmision'), '%d/%m/%Y').strftime('%Y-%m-%d')
                            except (ValueError, TypeError):
                                fecha_emision = None

                            # Insertar en tbl_estudios
                            cur.execute(
                                """
                                INSERT INTO tbl_estudios (
                                    id_usuario, id_universidad, id_grado_academico, titulo_profesional,
                                    especialidad, fecha_emision, resolucion, id_tipo_obtencion
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                                """,
                                (
                                    degree['user_id'],
                                    uni_id,
                                    id_grado_academico,
                                    degree.get('tituloProfesional'),
                                    degree.get('especialidad'),
                                    fecha_emision,
                                    degree.get('resolucion'),
                                    id_tipo_obtencion
                                )
                            )
                            total_degrees_inserted += 1
                        
                        conn.commit() # Confirmar la transacción para este usuario

                    except Exception as e:
                        print(f"\n   ❌ Error al procesar grados para el usuario: {e}")
                        conn.rollback() # Revertir si algo falla

            print(f"\n   ✅ Lote {i+1} completado.")
            
            if i < total_batches - 1:
                print(f"   ⏳ Esperando {DELAY_BETWEEN_BATCHES} segundos antes del siguiente lote...")
                time.sleep(DELAY_BETWEEN_BATCHES)

        print("\n--- RESUMEN DEL PROCESO ---")
        print(f"👤 Docentes procesados: {total_users}")
        print(f"🎓 Grados académicos encontrados: {total_degrees_found}")
        print(f"✍️ Registros de estudios insertados: {total_degrees_inserted}")
        print(f"🏫 Universidades en caché (nuevas y existentes): {len(university_cache)}")
        print("\n🎉 Proceso de poblado finalizado exitosamente!")

    except Exception as e:
        print(f"❌ Error crítico durante el proceso: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("🔌 Conexión a PostgreSQL cerrada.")

if __name__ == "__main__":
    # Opcional: Preguntar antes de limpiar la tabla para seguridad
    # choice = input("¿Desea limpiar la tabla 'tbl_estudios' antes de empezar? (s/N): ")
    # if choice.lower() == 's':
    #     print("🧹 Limpiando la tabla tbl_estudios...")
    #     try:
    #         conn = get_postgres_connection()
    #         cur = conn.cursor()
    #         cur.execute("TRUNCATE TABLE public.tbl_estudios RESTART IDENTITY;")
    #         conn.commit()
    #     except Exception as e:
    #         print(f"No se pudo limpiar la tabla: {e}")
    #     finally:
    #         if conn:
    #             conn.close()

    populate_sunedu_data_directly()
