import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio raíz al sys.path para importar db_connections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection, get_mysql_pilar3_connection

def migrar_coordinadores_historial():
    """
    Puebla la tabla tbl_coordinadores_historial basándose en el estado
    de los coordinadores y sus carreras asignadas.
    """
    print("--- Iniciando migración de TBL_COORDINADORES_HISTORIAL ---")
    
    mysql_conn = None
    pg_conn = None
    
    try:
        # 1. Obtener fechas de registro desde MySQL (tblSecres)
        mysql_conn = get_mysql_pilar3_connection()
        if not mysql_conn:
            raise Exception("No se pudo conectar a MySQL.")
            
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        mysql_cursor.execute("SELECT Id, FechReg FROM tblSecres")
        secres_data = mysql_cursor.fetchall()
        
        # Crear un diccionario para búsqueda rápida de fechas
        fechas_registro = {row['Id']: row['FechReg'] for row in secres_data}
        print(f"INFO: Se obtuvieron {len(fechas_registro)} fechas de registro desde MySQL.")

        # 2. Obtener asignaciones de coordinadores desde PostgreSQL
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("No se pudo conectar a PostgreSQL.")
            
        pg_cursor = pg_conn.cursor()
        
        # Limpiar la tabla de historial antes de insertar nuevos datos
        print("INFO: Limpiando la tabla tbl_coordinadores_historial...")
        pg_cursor.execute("TRUNCATE TABLE public.tbl_coordinadores_historial RESTART IDENTITY;")

        query_asignaciones = """
            SELECT
                c.id AS id_coordinador,
                c.estado_coordinador,
                cc.id_facultad,
                cc.id_carrera,
                cc.nivel_coordinador AS id_nivel_coordinador
            FROM
                public.tbl_coordinadores c
            JOIN
                public.tbl_coordinador_carrera cc ON c.id = cc.id_coordinador;
        """
        pg_cursor.execute(query_asignaciones)
        asignaciones = pg_cursor.fetchall()
        print(f"INFO: Se obtuvieron {len(asignaciones)} asignaciones de carrera para coordinadores desde PostgreSQL.")

        # 3. Procesar y generar los registros del historial
        historial_records = []
        
        for asignacion in asignaciones:
            id_coordinador, estado, id_facultad, id_carrera, id_nivel = asignacion
            
            # Obtener la fecha de registro; si no existe, usar la fecha actual.
            fecha_base = fechas_registro.get(id_coordinador, datetime.now())
            if not isinstance(fecha_base, datetime):
                fecha_base = datetime.now() # Fallback por si la fecha es inválida

            # CASO A: Coordinador ACTIVO (estado = 1)
            if estado == 1:
                # Registro 1: "Registro coordinador"
                historial_records.append((
                    id_coordinador, 0, fecha_base, None, None, 73, id_facultad, id_carrera, id_nivel
                ))
                # Registro 2: "Aceptacion del coordinador"
                historial_records.append((
                    id_coordinador, 1, fecha_base + timedelta(seconds=1), None, None, 74, id_facultad, id_carrera, id_nivel
                ))
            
            # CASO B: Coordinador INACTIVO (estado = 0)
            elif estado == 0:
                # Registro único: "Dimision del coordinador"
                historial_records.append((
                    id_coordinador, 0, fecha_base, None, None, 75, id_facultad, id_carrera, id_nivel
                ))

        print(f"INFO: Se generaron {len(historial_records)} registros para insertar en el historial.")

        # 4. Inserción masiva en PostgreSQL
        if historial_records:
            insert_query = """
                INSERT INTO public.tbl_coordinadores_historial (
                    id_coordinador, estado_coordinador_historial, fecha, 
                    numero_resolucion, comentario, id_accion, id_facultad, 
                    id_carrera, id_nivel_coordinador
                ) VALUES %s;
            """
            # Usar execute_values para una inserción masiva eficiente
            from psycopg2.extras import execute_values
            execute_values(pg_cursor, insert_query, historial_records)
            print(f"INFO: Se han insertado {len(historial_records)} registros en tbl_coordinadores_historial.")

        pg_conn.commit()
        print("¡Éxito! La migración de tbl_coordinadores_historial ha finalizado correctamente.")

    except Exception as e:
        print(f"ERROR: Ocurrió un error durante la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if mysql_cursor:
            mysql_cursor.close()
        if mysql_conn:
            mysql_conn.close()
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()
        print("--- Fin de la migración de TBL_COORDINADORES_HISTORIAL ---")

if __name__ == '__main__':
    migrar_coordinadores_historial()
