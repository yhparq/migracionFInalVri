import sys
import os
from datetime import datetime, timedelta
from psycopg2.extras import execute_values

# Añadir el directorio raíz al sys.path para importar db_connections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection, get_mysql_pilar3_connection

def migrar_coordinadores_historial():
    """
    Puebla la tabla tbl_coordinadores_historial basándose en el estado final
    de los coordinadores en tbl_coordinadores.
    Lógica de estados:
    - 0 (Registrado): Crea 1 registro de historial.
    - 1 (Aceptado): Crea 2 registros (registrado -> aceptado).
    - 2 (Dimisión): Crea 2 registros (registrado -> dimisión).
    """
    print("--- Iniciando migración de TBL_COORDINADORES_HISTORIAL (Lógica Corregida) ---")
    
    mysql_conn = None
    pg_conn = None
    
    try:
        # 1. Conexiones a las bases de datos
        mysql_conn = get_mysql_pilar3_connection()
        pg_conn = get_postgres_connection()
        if not mysql_conn or not pg_conn:
            raise Exception("No se pudieron establecer las conexiones a las bases de datos.")
            
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        pg_cursor = pg_conn.cursor()

        # 2. Obtener IDs de acciones desde PostgreSQL
        print("INFO: Obteniendo IDs de acciones para el historial de coordinadores...")
        pg_cursor.execute("""
            SELECT nombre, id FROM public.dic_acciones 
            WHERE nombre IN ('Registro coordinador', 'Aceptacion del coordinador', 'Dimision del coordinador')
        """)
        acciones = dict(pg_cursor.fetchall())
        
        id_accion_registro = acciones.get('Registro coordinador')
        id_accion_aceptacion = acciones.get('Aceptacion del coordinador')
        id_accion_dimision = acciones.get('Dimision del coordinador')

        if not all([id_accion_registro, id_accion_aceptacion, id_accion_dimision]):
            raise Exception("No se encontraron todas las acciones requeridas para el historial de coordinadores.")
        
        print(f"INFO: IDs de acciones -> Registro: {id_accion_registro}, Aceptación: {id_accion_aceptacion}, Dimisión: {id_accion_dimision}")

        # 3. Obtener fechas de registro desde MySQL (tblSecres)
        print("INFO: Extrayendo fechas de registro desde MySQL (tblSecres)...")
        mysql_cursor.execute("SELECT Id, FechReg FROM tblSecres")
        fechas_registro_map = {row['Id']: row['FechReg'] for row in mysql_cursor.fetchall()}
        print(f"INFO: Se obtuvieron {len(fechas_registro_map)} fechas de registro.")

        # 4. Obtener los coordinadores actuales desde PostgreSQL
        print("INFO: Obteniendo coordinadores desde PostgreSQL (tbl_coordinadores)...")
        pg_cursor.execute("SELECT id, estado_coordinador FROM public.tbl_coordinadores")
        coordinadores_pg = pg_cursor.fetchall()
        print(f"INFO: Se encontraron {len(coordinadores_pg)} coordinadores para procesar.")

        # 5. Procesar y generar los registros del historial
        historial_records = []
        
        for id_coordinador, estado in coordinadores_pg:
            fecha_registro = fechas_registro_map.get(id_coordinador) or datetime.now()
            if not fechas_registro_map.get(id_coordinador):
                print(f"ADVERTENCIA: No se encontró fecha para el coordinador {id_coordinador}. Se usará la fecha actual.")

            # Siempre se crea el evento de "Registro" primero
            historial_records.append((
                id_coordinador, 0, fecha_registro, None, None, id_accion_registro, None, None, None
            ))

            # Si está aceptado, se añade el segundo evento
            if estado == 1:
                historial_records.append((
                    id_coordinador, 1, fecha_registro + timedelta(seconds=1), None, None, id_accion_aceptacion, None, None, None
                ))
            # Si es dimisión, se añade el segundo evento
            elif estado == 2:
                historial_records.append((
                    id_coordinador, 2, fecha_registro + timedelta(seconds=1), None, None, id_accion_dimision, None, None, None
                ))

        print(f"INFO: Se generaron {len(historial_records)} registros para el historial.")

        # 6. Inserción masiva en PostgreSQL
        if historial_records:
            print("INFO: Limpiando la tabla tbl_coordinadores_historial...")
            pg_cursor.execute("TRUNCATE TABLE public.tbl_coordinadores_historial RESTART IDENTITY;")

            print("INFO: Iniciando carga masiva de datos en el historial...")
            insert_query = """
                INSERT INTO public.tbl_coordinadores_historial (
                    id_coordinador, estado_coordinador_historial, fecha, 
                    numero_resolucion, comentario, id_accion, id_facultad, 
                    id_carrera, id_nivel_coordinador
                ) VALUES %s;
            """
            execute_values(pg_cursor, insert_query, historial_records)
            print(f"¡Éxito! Se han insertado {len(historial_records)} registros en tbl_coordinadores_historial.")
        else:
            print("INFO: No hay registros de historial para insertar.")

        pg_conn.commit()

    except Exception as e:
        print(f"ERROR: Ocurrió un error durante la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if mysql_cursor: mysql_cursor.close()
        if mysql_conn: mysql_conn.close()
        if pg_cursor: pg_cursor.close()
        if pg_conn: pg_conn.close()
        print("--- Fin de la migración de TBL_COORDINADORES_HISTORIAL ---")

if __name__ == '__main__':
    migrar_coordinadores_historial()