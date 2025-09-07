import psycopg2
import sys
import os
import io
import re
from datetime import datetime
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def parse_fecha_from_obs(obs_text, fallback_date):
    if not obs_text:
        return fallback_date
    match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', obs_text)
    if match:
        try:
            datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
            return match.group(1)
        except ValueError:
            return fallback_date
    return fallback_date

def migrate_tbl_docentes_lineas_historial():
    """
    Migra el historial de líneas de investigación de docentes, validando
    la existencia de la sublínea de investigación antes de insertar.
    """
    print("--- Iniciando migración de tbl_docentes_lineas_historial ---")
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()

        if pg_conn is None or mysql_conn is None:
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur = mysql_conn.cursor(dictionary=True)

        print("  Paso 1: Creando mapas y sets de validación...")
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docentes_map = {row[1]: row[0] for row in pg_cur.fetchall()}
        
        # MEJORA: Cargar los IDs de sublíneas válidas para validación
        pg_cur.execute("SELECT id FROM tbl_sublineas_vri")
        valid_sublineas = {row[0] for row in pg_cur.fetchall()}
        print(f"  Se mapearon {len(docentes_map)} docentes y {len(valid_sublineas)} sublíneas válidas.")

        print("  Paso 2: Leyendo datos de origen desde docLineas (MySQL)...")
        mysql_cur.execute("SELECT IdDocente, IdLinea, Estado, Fecha, Obs FROM docLineas")
        source_data = mysql_cur.fetchall()
        print(f"  Se encontraron {len(source_data)} registros para procesar.")

        print("  Paso 3: Procesando y transformando datos...")
        data_for_copy = []
        unmatched_docentes = 0
        invalid_sublineas = 0

        for row in source_data:
            id_linea = row['IdLinea']
            # MEJORA: Validar que la sublínea exista en la tabla de destino
            if id_linea not in valid_sublineas:
                invalid_sublineas += 1
                continue

            id_docente_antiguo = row['IdDocente']
            new_docente_id = docentes_map.get(id_docente_antiguo)

            if not new_docente_id:
                unmatched_docentes += 1
                continue

            estado_val = row['Estado']
            fecha_original = row['Fecha']
            if not fecha_original or str(fecha_original) == '0000-00-00 00:00:00':
                fecha_original = datetime.now()
            
            obs_text = row['Obs']

            if estado_val == 1:
                data_for_copy.append((new_docente_id, id_linea, estado_val, fecha_original, None, 1))
            elif estado_val in [0, 2]:
                fecha_registro_obs = parse_fecha_from_obs(obs_text, fecha_original)
                data_for_copy.append((new_docente_id, id_linea, estado_val, fecha_registro_obs, None, 1))
                data_for_copy.append((new_docente_id, id_linea, 1, fecha_original, None, 0))

        print(f"  Se prepararon {len(data_for_copy)} registros para la carga masiva.")
        if unmatched_docentes > 0:
            print(f"  ADVERTENCIA: Se ignoraron {unmatched_docentes} registros por docente no mapeado.")
        if invalid_sublineas > 0:
            print(f"  ADVERTENCIA: Se ignoraron {invalid_sublineas} registros por sublínea de investigación inválida.")

        if data_for_copy:
            print("  Paso 4: Cargando datos en PostgreSQL con COPY...")
            buffer = io.StringIO()
            for record in data_for_copy:
                line = '\t'.join(str(item) if item is not None else '\\N' for item in record)
                buffer.write(line + '\n')
            
            buffer.seek(0)
            
            columns = ('id_docente', 'id_sublinea_vri', 'id_estado_historial', 
                       'fecha_registro', 'numero_resolucion', 'estado')
            
            pg_cur.copy_expert(
                sql=f"COPY public.tbl_docentes_lineas_historial ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')",
                file=buffer
            )
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {len(data_for_copy)} registros.")

        print("--- Migración de tbl_docentes_lineas_historial completada con éxito. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_docentes_lineas_historial()