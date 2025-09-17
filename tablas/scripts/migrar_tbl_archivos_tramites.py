import io
import os
import sys
import pandas as pd
import psycopg2
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=dotenv_path)

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def migrate_tbl_archivos_tramites():
    """
    Migra, renombra y sube archivos de trámites a Supabase Storage.
    
    - Genera un nuevo nombre de archivo estructurado.
    - Renombra el archivo físico en el disco local.
    - Sube el archivo renombrado a un bucket de Supabase en una carpeta específica del trámite.
    - Guarda la referencia en la base de datos PostgreSQL sin la ruta completa.
    """
    mysql_conn = get_mysql_pilar3_connection()
    postgres_conn = get_postgres_connection()
    
    # --- Configuración de Supabase ---
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    bucket_name = "tramites-documentos"
    
    source_files_path = "/Users/nachiparra/Documents/tesis/docs"

    if not all([mysql_conn, postgres_conn, url, key]):
        print("Error: Faltan conexiones a la base de datos o credenciales de Supabase en .env.")
        return

    try:
        print("--- Iniciando migración, renombrado y subida de archivos de trámites ---")

        # 1. Obtener mapeos desde PostgreSQL
        print("  Paso 1: Obteniendo mapeos desde PostgreSQL...")
        with postgres_conn.cursor() as cursor:
            cursor.execute("SELECT id, id_antiguo, codigo_proyecto FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
            tramites_map = {row[1]: {'id': row[0], 'codigo': row[2]} for row in cursor.fetchall()}
            cursor.execute("SELECT id_tramite, id FROM tbl_tramites_metadatos ORDER BY id ASC")
            metadatos_map = {row[0]: row[1] for row in cursor.fetchall()}
        print("  Mapeos obtenidos correctamente.")

        # 2. Extraer datos desde MySQL
        print("  Paso 2: Extrayendo datos de tesTramsDet desde MySQL...")
        df_mysql = pd.read_sql("SELECT IdTramite, Iteracion, Archivo, Fecha FROM tesTramsDet", mysql_conn)
        print(f"  Se extrajeron {len(df_mysql)} registros de archivos desde MySQL.")

        # 3. Procesar, renombrar y subir archivos
        print("  Paso 3: Procesando, renombrando y subiendo archivos...")
        archivos_list = []
        omitted_tramite_map, omitted_metadato_map, omitted_iteracion = 0, 0, 0
        renamed_count, rename_errors, uploaded_count, upload_errors = 0, 0, 0, 0
        version_tracker = {}

        for _, row in df_mysql.iterrows():
            id_tramite_antiguo = int(row['IdTramite'])
            iteracion = row['Iteracion']
            original_filename = row['Archivo']

            tramite_info = tramites_map.get(id_tramite_antiguo)
            if not tramite_info:
                omitted_tramite_map += 1
                continue
            
            id_tramite_nuevo = tramite_info['id']
            codigo_proyecto_original = tramite_info['codigo']
            codigo_proyecto_limpio = codigo_proyecto_original.replace('T-', '') if codigo_proyecto_original else ''

            id_metadato = metadatos_map.get(id_tramite_nuevo)
            if not id_metadato:
                omitted_metadato_map += 1
                continue

            if iteracion == 1: id_etapa = 1
            elif iteracion in [2, 3]: id_etapa = 7
            elif iteracion == 4: id_etapa = 10
            elif iteracion == 5: id_etapa = 16
            else:
                omitted_iteracion += 1
                continue

            if iteracion in [1, 2, 3]: id_tipo_archivo = 1
            elif iteracion in [4, 5]: id_tipo_archivo = 9
            else: continue

            version_key = (id_tramite_nuevo, id_tipo_archivo)
            current_version_char_code = version_tracker.get(version_key, ord('A'))
            version_letter = chr(current_version_char_code)
            version_tracker[version_key] = current_version_char_code + 1

            year_part = pd.to_datetime(row['Fecha']).strftime('%y') if pd.notna(row['Fecha']) else "00"
            _, extension = os.path.splitext(original_filename)
            nuevo_nombre_archivo = f"{version_letter}{id_tipo_archivo}-P{year_part}-{codigo_proyecto_limpio}{extension}"

            original_file_path = os.path.join(source_files_path, original_filename)
            new_file_path = os.path.join(source_files_path, nuevo_nombre_archivo)

            if os.path.exists(original_file_path):
                try:
                    os.rename(original_file_path, new_file_path)
                    renamed_count += 1
                    
                    supabase_path = f"tramite-{id_tramite_nuevo}/{nuevo_nombre_archivo}"
                    with open(new_file_path, 'rb') as f:
                        supabase.storage.from_(bucket_name).upload(file=f, path=supabase_path)
                    uploaded_count += 1

                    archivos_list.append({
                        'id_tramite': id_tramite_nuevo, 'id_etapa': id_etapa,
                        'id_tramites_metadatos': id_metadato, 'id_tipo_archivo': id_tipo_archivo,
                        'nombre_archivo': nuevo_nombre_archivo, 'storage': 'supabase',
                        'bucket': bucket_name, 'fecha': row['Fecha'], 'estado_archivo': 1
                    })

                except OSError as e:
                    print(f"    ERROR al renombrar '{original_filename}': {e}")
                    rename_errors += 1
                except Exception as e:
                    print(f"    ERROR al subir '{nuevo_nombre_archivo}' a Supabase: {e}")
                    upload_errors += 1
            
        print(f"  Transformación completada. Se generaron {len(archivos_list)} registros para la BD.")
        print(f"  Resumen de renombrado: {renamed_count} archivos renombrados, {rename_errors} errores.")
        print(f"  Resumen de subida: {uploaded_count} archivos subidos, {upload_errors} errores.")
        if omitted_tramite_map > 0: print(f"  Advertencia: {omitted_tramite_map} registros omitidos por no encontrar mapeo de trámite.")
        if omitted_metadato_map > 0: print(f"  Advertencia: {omitted_metadato_map} registros omitidos por no encontrar metadato asociado.")
        if omitted_iteracion > 0: print(f"  Advertencia: {omitted_iteracion} registros omitidos por tener una 'Iteracion' no válida.")

        if not archivos_list:
            print("No hay datos de archivos para migrar.")
            return

        # 4. Cargar datos en PostgreSQL
        df_final = pd.DataFrame(archivos_list)
        
        print("  Paso 4: Iniciando carga de datos a tbl_archivos_tramites...")
        buffer = io.StringIO()
        df_final.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
        buffer.seek(0)

        with postgres_conn.cursor() as cursor:
            print("    Limpiando la tabla tbl_archivos_tramites...")
            cursor.execute("TRUNCATE TABLE public.tbl_archivos_tramites RESTART IDENTITY CASCADE;")
            
            print("    Cargando nuevos datos...")
            cursor.copy_expert(
                sql=r"""
                    COPY public.tbl_archivos_tramites ( 
                        id_tramite, id_etapa, id_tramites_metadatos, id_tipo_archivo, 
                        nombre_archivo, storage, bucket, fecha, estado_archivo 
                    ) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
                """, 
                file=buffer
            )
        postgres_conn.commit()
        print(f"  Carga masiva completada. Se han migrado {len(df_final)} registros.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error durante la migración de archivos de trámites: {error}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("--- Migración de archivos de trámites finalizada. ---")

if __name__ == "__main__":
    migrate_tbl_archivos_tramites()
