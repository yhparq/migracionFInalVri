import io
import os
import sys
import pandas as pd
import psycopg2

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def migrate_tbl_programacion_sustentacion():
    """
    Migra los datos de programación de sustentaciones desde tesSustensSolic y
    tesSustens (MySQL) a tbl_programacion_sustentacion (PostgreSQL).
    """
    mysql_conn = get_mysql_pilar3_connection()
    postgres_conn = get_postgres_connection()

    if not all([mysql_conn, postgres_conn]):
        print("Error: No se pudieron establecer las conexiones a la base de datos.")
        return

    try:
        print("--- Iniciando migración de Programación de Sustentaciones ---")

        # 1. Obtener mapeo de IDs de trámites desde PostgreSQL
        print("  Paso 1: Obteniendo mapeo de trámites desde PostgreSQL...")
        df_tramites_map = pd.read_sql("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL", postgres_conn)
        tramites_map = df_tramites_map.set_index('id_antiguo')['id'].to_dict()
        print("  Mapeo de trámites obtenido.")

        # 2. Extraer y unir datos de MySQL
        print("  Paso 2: Extrayendo y uniendo datos de tesSustensSolic y tesSustens desde MySQL...")
        query_mysql = """
            SELECT
                sol.IdTramite,
                sol.FechSusten,
                sol.DateModif,
                sol.DateSolic,
                sus.Lugar
            FROM
                tesSustensSolic sol
            JOIN
                tesSustens sus ON sol.IdTramite = sus.IdTramite;
        """
        df_mysql = pd.read_sql(query_mysql, mysql_conn)
        # Eliminar duplicados por si un trámite tiene múltiples entradas, quedándonos con la más reciente
        df_mysql.drop_duplicates(subset=['IdTramite'], keep='last', inplace=True)
        print(f"  Se extrajeron {len(df_mysql)} registros únicos de programación.")

        # 3. Transformar datos y aplicar la lógica de negocio
        print("  Paso 3: Transformando datos...")
        programaciones_list = []
        omitted_count = 0

        for _, row in df_mysql.iterrows():
            id_tramite_antiguo = row['IdTramite']
            id_tramite_nuevo = tramites_map.get(id_tramite_antiguo)

            if not id_tramite_nuevo:
                omitted_count += 1
                continue

            # Lógica de fallback para fechas inválidas (ej. '0000-00-00')
            fecha_sustentacion = row['FechSusten']
            if pd.isna(fecha_sustentacion) or str(fecha_sustentacion) == '0000-00-00':
                fecha_sustentacion = row['DateSolic'] # Usar fecha de solicitud como fallback
            if pd.isna(fecha_sustentacion):
                fecha_sustentacion = pd.Timestamp.now() # Último recurso

            programaciones_list.append({
                'id_tramite': id_tramite_nuevo,
                'fecha_sustentacion': fecha_sustentacion,
                'hora_sustentacion': pd.to_datetime(row['DateModif']).time(),
                'lugar_sustentacion': row['Lugar'],
                'fecha_registro': row['DateSolic'],
                'estado': 1
            })

        print(f"  Transformación completada. Se generaron {len(programaciones_list)} registros para insertar.")
        if omitted_count > 0:
            print(f"  Advertencia: {omitted_count} registros omitidos por no encontrar mapeo de trámite.")

        if not programaciones_list:
            print("No hay datos de programación para migrar.")
            return

        # 4. Cargar datos en PostgreSQL
        df_final = pd.DataFrame(programaciones_list)
        
        print("  Paso 4: Iniciando carga de datos a tbl_programacion_sustentacion...")
        
        with postgres_conn.cursor() as cursor:
            print("    Limpiando la tabla tbl_programacion_sustentacion...")
            cursor.execute("TRUNCATE TABLE public.tbl_programacion_sustentacion RESTART IDENTITY CASCADE;")

            buffer = io.StringIO()
            df_final.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
            buffer.seek(0)

            cursor.copy_expert(
                sql=r"""
                    COPY public.tbl_programacion_sustentacion (
                        id_tramite, fecha_sustentacion, hora_sustentacion,
                        lugar_sustentacion, fecha_registro, estado
                    ) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
                """,
                file=buffer
            )
            print(f"    Carga masiva completada. Se han insertado {len(df_final)} registros.")

        postgres_conn.commit()

    except (Exception, psycopg2.Error) as error:
        print(f"Error durante la migración de programación de sustentaciones: {error}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("--- Migración de Programación de Sustentaciones finalizada. ---")

if __name__ == "__main__":
    migrate_tbl_programacion_sustentacion()
