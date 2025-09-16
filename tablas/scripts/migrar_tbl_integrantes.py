import io
import os
import sys
import pandas as pd
import psycopg2

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def migrate_tbl_integrantes():
    """
    Migra los integrantes de los trámites desde la tabla tesTramites (MySQL)
    a la tabla tbl_integrantes (PostgreSQL).
    """
    mysql_conn = get_mysql_pilar3_connection()
    postgres_conn = get_postgres_connection()

    if not all([mysql_conn, postgres_conn]):
        print("Error: No se pudieron establecer las conexiones a la base de datos.")
        return

    try:
        # 1. Obtener mapeos de IDs desde PostgreSQL
        print("Obteniendo mapeos de IDs desde PostgreSQL...")
        df_tramites_map = pd.read_sql("SELECT id, id_antiguo FROM tbl_tramites", postgres_conn)
        tramites_map = df_tramites_map.set_index('id_antiguo')['id'].to_dict()

        df_tesistas_map = pd.read_sql("SELECT id, id_antiguo FROM tbl_tesistas", postgres_conn)
        tesistas_map = df_tesistas_map.set_index('id_antiguo')['id'].to_dict()
        print("Mapeos de IDs obtenidos correctamente.")

        # 2. Extraer datos de trámites desde MySQL
        print("Extrayendo datos de tesTramites desde MySQL...")
        df_tramites_mysql = pd.read_sql(
            "SELECT Id, IdTesista1, IdTesista2, FechRegProy FROM tesTramites",
            mysql_conn
        )
        print(f"Se extrajeron {len(df_tramites_mysql)} trámites desde MySQL.")

        # 3. Transformar datos para crear la lista de integrantes
        print("Transformando datos para la tabla de integrantes...")
        integrantes_data = []
        registros_omitidos = 0
        tramites_sin_mapeo = 0
        tesistas_sin_mapeo = 0

        for _, row in df_tramites_mysql.iterrows():
            id_tramite_antiguo = row['Id']
            id_tesista1_antiguo = row['IdTesista1']
            id_tesista2_antiguo = row['IdTesista2']
            fecha_registro = row['FechRegProy'] if pd.notna(row['FechRegProy']) else pd.Timestamp.now()

            id_tramite_nuevo = tramites_map.get(id_tramite_antiguo)

            if not id_tramite_nuevo:
                tramites_sin_mapeo += 1
                continue

            # Procesar Tesista 1
            if id_tesista1_antiguo and id_tesista1_antiguo > 0:
                id_tesista1_nuevo = tesistas_map.get(id_tesista1_antiguo)
                if id_tesista1_nuevo:
                    integrantes_data.append({
                        'id_tramite': id_tramite_nuevo,
                        'id_tesista': id_tesista1_nuevo,
                        'tipo_integrante': 1,
                        'fecha_registro': fecha_registro,
                        'estado_integrante': 1
                    })
                else:
                    tesistas_sin_mapeo += 1
            
            # Procesar Tesista 2
            if id_tesista2_antiguo and id_tesista2_antiguo > 0:
                id_tesista2_nuevo = tesistas_map.get(id_tesista2_antiguo)
                if id_tesista2_nuevo:
                    integrantes_data.append({
                        'id_tramite': id_tramite_nuevo,
                        'id_tesista': id_tesista2_nuevo,
                        'tipo_integrante': 2,
                        'fecha_registro': fecha_registro,
                        'estado_integrante': 1
                    })
                else:
                    tesistas_sin_mapeo += 1

        print(f"Transformación completada. Se generaron {len(integrantes_data)} registros para integrantes.")
        if tramites_sin_mapeo > 0:
            print(f"Advertencia: Se omitieron {tramites_sin_mapeo} trámites porque no se encontró su mapeo de ID.")
        if tesistas_sin_mapeo > 0:
            print(f"Advertencia: Se omitieron {tesistas_sin_mapeo} tesistas porque no se encontró su mapeo de ID.")

        if not integrantes_data:
            print("No hay datos de integrantes para migrar.")
            return

        # 4. Cargar datos en PostgreSQL usando COPY
        df_integrantes = pd.DataFrame(integrantes_data)
        
        # Reordenar columnas para que coincidan con la tabla de destino
        df_integrantes = df_integrantes[[
            'id_tramite', 'id_tesista', 'tipo_integrante', 
            'fecha_registro', 'estado_integrante'
        ]]

        print("Iniciando carga masiva a tbl_integrantes en PostgreSQL...")
        buffer = io.StringIO()
        df_integrantes.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
        buffer.seek(0)

        with postgres_conn.cursor() as cursor:
            cursor.copy_expert(
                sql=r"""
                    COPY public.tbl_integrantes (
                        id_tramite, id_tesista, tipo_integrante,
                        fecha_registro, estado_integrante
                    ) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
                """,
                file=buffer
            )
        postgres_conn.commit()
        print(f"Carga masiva completada. Se han migrado {len(df_integrantes)} registros a tbl_integrantes.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error durante la migración de integrantes: {error}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("Conexiones a las bases de datos cerradas.")

if __name__ == "__main__":
    migrate_tbl_integrantes()
