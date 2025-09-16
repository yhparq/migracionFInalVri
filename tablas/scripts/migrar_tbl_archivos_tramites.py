import io
import os
import sys
import pandas as pd
import psycopg2

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def migrate_tbl_archivos_tramites():
    """
    Migra los archivos de trámites desde tesTramsDet (MySQL) a tbl_archivos_tramites (PostgreSQL).
    
    La lógica de mapeo para 'id_etapa' y 'id_tipo_archivo' se basa en la columna 'Iteracion'.
    El 'id_tramites_metadatos' se busca a partir del nuevo 'id_tramite'.
    """
    mysql_conn = get_mysql_pilar3_connection()
    postgres_conn = get_postgres_connection()

    if not all([mysql_conn, postgres_conn]):
        print("Error: No se pudieron establecer las conexiones a la base de datos.")
        return

    try:
        print("--- Iniciando migración de archivos de trámites ---")

        # 1. Obtener mapeos de IDs desde PostgreSQL (lógica idéntica a tramites_det)
        print("  Paso 1: Obteniendo mapeos desde PostgreSQL...")
        with postgres_conn.cursor() as cursor:
            # LÓGICA DE CORRECCIÓN: Usar el mismo método que el script que sí funciona.
            # Si hay duplicados, este método se quedará con el último, que es el
            # comportamiento que se debe replicar.
            cursor.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
            tramites_map = {row[1]: row[0] for row in cursor.fetchall()}

            # Mapeo de metadatos: id_tramite (PostgreSQL) -> id (tbl_tramites_metadatos)
            cursor.execute("SELECT id_tramite, id FROM tbl_tramites_metadatos ORDER BY id ASC")
            metadatos_map = {row[0]: row[1] for row in cursor.fetchall()}
        
        print("  Mapeos obtenidos correctamente.")

        # 2. Extraer datos de archivos desde MySQL
        print("  Paso 2: Extrayendo datos de tesTramsDet desde MySQL...")
        df_mysql = pd.read_sql(
            "SELECT IdTramite, Iteracion, Archivo, Fecha FROM tesTramsDet",
            mysql_conn
        )
        print(f"  Se extrajeron {len(df_mysql)} registros de archivos desde MySQL.")

        # 3. Transformar datos y aplicar la lógica de negocio
        print("  Paso 3: Transformando datos y aplicando lógica...")
        archivos_list = []
        omitted_tramite_map = 0
        omitted_metadato_map = 0
        omitted_iteracion = 0

        for _, row in df_mysql.iterrows():
            # Forzar la conversión a entero también en el valor de búsqueda para asegurar la coincidencia de tipos
            id_tramite_antiguo = int(row['IdTramite'])
            iteracion = row['Iteracion']
            
            id_tramite_nuevo = tramites_map.get(id_tramite_antiguo)
            if not id_tramite_nuevo:
                omitted_tramite_map += 1
                continue

            id_metadato = metadatos_map.get(id_tramite_nuevo)
            if not id_metadato:
                omitted_metadato_map += 1
                continue

            # Lógica para id_etapa
            if iteracion == 1:
                id_etapa = 1
            elif iteracion in [2, 3]:
                id_etapa = 7
            elif iteracion == 4:
                id_etapa = 10
            elif iteracion == 5:
                id_etapa = 16
            else:
                omitted_iteracion += 1
                continue

            # Lógica para id_tipo_archivo
            if iteracion in [1, 2, 3]:
                id_tipo_archivo = 1
            elif iteracion in [4, 5]:
                id_tipo_archivo = 9
            else:
                # Esto ya está cubierto por el continue anterior, pero es una salvaguarda
                continue

            archivos_list.append({
                'id_tramite': id_tramite_nuevo,
                'id_etapa': id_etapa,
                'id_tramites_metadatos': id_metadato,
                'id_tipo_archivo': id_tipo_archivo,
                'nombre_archivo': row['Archivo'],
                'storage': 'supabase',
                'bucket': 'tramites_documentos',
                'fecha': row['Fecha'],
                'estado_archivo': 1
            })

        print(f"  Transformación completada. Se generaron {len(archivos_list)} registros para insertar.")
        if omitted_tramite_map > 0:
            print(f"  Advertencia: {omitted_tramite_map} registros omitidos por no encontrar mapeo de trámite.")
        if omitted_metadato_map > 0:
            print(f"  Advertencia: {omitted_metadato_map} registros omitidos por no encontrar metadato asociado.")
        if omitted_iteracion > 0:
            print(f"  Advertencia: {omitted_iteracion} registros omitidos por tener una 'Iteracion' no válida.")

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
