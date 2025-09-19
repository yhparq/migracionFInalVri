import io
import os
import sys
import pandas as pd
import psycopg2
from collections import defaultdict

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def migrate_tbl_archivos_tramites():
    """
    Script 1/2: Migra referencias de archivos, los renombra localmente y guarda en la BD.
    - Lee la tabla de archivos de MySQL.
    - Mapea IDs de trámite y metadatos de forma precisa.
    - Genera un nuevo nombre de archivo estandarizado.
    - Renombra el archivo físico en el disco local.
    - Guarda la referencia en PostgreSQL con estado 'local'.
    """
    mysql_conn = get_mysql_pilar3_connection()
    postgres_conn = get_postgres_connection()
    
    # IMPORTANTE: Ruta donde se encuentran los archivos originales.
    source_files_path = "/Users/nachiparra/Documents/tesis/docs"

    if not all([mysql_conn, postgres_conn]):
        print("Error: Faltan conexiones a la base de datos.")
        return

    try:
        print("--- Iniciando Migración y Renombrado Local de Archivos ---")

        # 1. Obtener mapeos desde PostgreSQL
        print("  Paso 1: Obteniendo mapeos desde PostgreSQL...")
        with postgres_conn.cursor() as cursor:
            cursor.execute("SELECT id, id_antiguo, codigo_proyecto FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
            tramites_map = {row[1]: {'id': row[0], 'codigo': row[2]} for row in cursor.fetchall()}
            
            # Mapa de metadatos mejorado: (id_tramite, id_etapa) -> id_metadato
            cursor.execute("SELECT id, id_tramite, id_etapa FROM tbl_tramites_metadatos")
            metadatos_data = cursor.fetchall()
            metadatos_map = {(row[1], row[2]): row[0] for row in metadatos_data}
            
            # Fallback map por si la etapa no coincide
            metadatos_fallback_map = defaultdict(list)
            for mid, m_tid, m_eid in metadatos_data:
                metadatos_fallback_map[m_tid].append({'id': mid, 'id_etapa': m_eid})

        print("  Mapeos obtenidos correctamente.")

        # 2. Extraer datos desde MySQL
        print("  Paso 2: Extrayendo datos de tesTramsDet desde MySQL...")
        df_mysql = pd.read_sql("SELECT IdTramite, Iteracion, Archivo, Fecha FROM tesTramsDet", mysql_conn)
        print(f"  Se extrajeron {len(df_mysql)} registros de archivos desde MySQL.")

        # 3. Procesar y renombrar archivos
        print("  Paso 3: Procesando y renombrando archivos localmente...")
        archivos_list = []
        omitted_tramite_map, omitted_metadato_map, omitted_iteracion = 0, 0, 0
        renamed_count, rename_errors = 0, 0
        version_tracker = defaultdict(lambda: ord('A'))

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

            # Lógica de mapeo de Etapa y Tipo de Archivo basada en Iteracion
            id_etapa_candidata = None
            id_tipo_archivo = None
            if iteracion == 1: id_etapa_candidata = 1; id_tipo_archivo = 1
            elif iteracion in [2, 3]: id_etapa_candidata = 7; id_tipo_archivo = 1
            elif iteracion == 4: id_etapa_candidata = 10; id_tipo_archivo = 9
            elif iteracion == 5: id_etapa_candidata = 16; id_tipo_archivo = 9
            else:
                omitted_iteracion += 1
                continue

            # Búsqueda precisa del metadato
            id_metadato = metadatos_map.get((id_tramite_nuevo, id_etapa_candidata))
            id_etapa_final = id_etapa_candidata
            
            if not id_metadato and metadatos_fallback_map.get(id_tramite_nuevo):
                primer_metadato = metadatos_fallback_map[id_tramite_nuevo][0]
                id_metadato = primer_metadato['id']
                id_etapa_final = primer_metadato['id_etapa']
            
            if not id_metadato:
                omitted_metadato_map += 1
                continue

            # Generación del nuevo nombre
            version_key = (id_tramite_nuevo, id_tipo_archivo)
            version_letter = chr(version_tracker[version_key])
            version_tracker[version_key] += 1

            year_part = pd.to_datetime(row['Fecha']).strftime('%y') if pd.notna(row['Fecha']) else "00"
            _, extension = os.path.splitext(original_filename)
            nuevo_nombre_archivo = f"{version_letter}{id_tipo_archivo}-P{year_part}-{codigo_proyecto_limpio}{extension}"

            original_file_path = os.path.join(source_files_path, original_filename)
            new_file_path = os.path.join(source_files_path, nuevo_nombre_archivo)

            if os.path.exists(original_file_path):
                try:
                    os.rename(original_file_path, new_file_path)
                    renamed_count += 1
                    
                    archivos_list.append({
                        'id_tramite': id_tramite_nuevo, 'id_etapa': id_etapa_final,
                        'id_tramites_metadatos': id_metadato, 'id_tipo_archivo': id_tipo_archivo,
                        'nombre_archivo': nuevo_nombre_archivo, 'storage': 'local',
                        'bucket': source_files_path, 'fecha': row['Fecha'], 'estado_archivo': 1
                    })

                except OSError as e:
                    print(f"    ERROR al renombrar '{original_filename}': {e}")
                    rename_errors += 1
            
        print(f"  Transformación completada. Se generaron {len(archivos_list)} registros para la BD.")
        print(f"  Resumen de renombrado: {renamed_count} archivos renombrados, {rename_errors} errores.")
        if omitted_tramite_map > 0: print(f"  Advertencia: {omitted_tramite_map} omitidos (sin mapeo de trámite).")
        if omitted_metadato_map > 0: print(f"  Advertencia: {omitted_metadato_map} omitidos (sin metadato asociado).")
        if omitted_iteracion > 0: print(f"  Advertencia: {omitted_iteracion} omitidos (iteración no válida).")

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
        print(f"Error durante la migración local de archivos: {error}")
        if postgres_conn: postgres_conn.rollback()
    finally:
        if mysql_conn and mysql_conn.is_connected(): mysql_conn.close()
        if postgres_conn: postgres_conn.close()
        print("--- Migración y Renombrado Local de Archivos finalizada. ---")

if __name__ == "__main__":
    migrate_tbl_archivos_tramites()
