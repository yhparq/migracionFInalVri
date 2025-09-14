import sys
import os
from collections import defaultdict

# Añadir el directorio raíz al sys.path para poder importar db_connections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection, get_mysql_pilar3_connection
from psycopg2.extras import execute_values

def migrar_tbl_coordinador_carrera():
    """
    Migra los datos desde tblSecres (MySQL) a tbl_coordinador_carrera (PostgreSQL)
    con la lógica de asignación de carreras por facultad.
    """
    print("--- Iniciando migración de TBL_COORDINADOR_CARRERA ---")
    
    pg_conn = None
    mysql_conn = None
    
    try:
        # 1. Conexión a las bases de datos
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()
        
        if not pg_conn or not mysql_conn:
            raise Exception("No se pudieron establecer las conexiones a las bases de datos.")
            
        pg_cursor = pg_conn.cursor()
        mysql_cursor = mysql_conn.cursor(dictionary=True)

        # 2. Obtener el mapa de carreras por facultad desde PostgreSQL
        print("INFO: Obteniendo mapa de carreras por facultad desde PostgreSQL...")
        pg_cursor.execute("SELECT id, id_facultad FROM public.dic_carreras WHERE estado_carrera = 1")
        carreras_pg = pg_cursor.fetchall()
        
        carreras_por_facultad = defaultdict(list)
        for id_carrera, id_facultad in carreras_pg:
            carreras_por_facultad[id_facultad].append(id_carrera)
        
        print(f"INFO: Se encontraron {len(carreras_pg)} carreras activas distribuidas en {len(carreras_por_facultad)} facultades.")

        # 3. Extraer datos de coordinadores desde MySQL (tblSecres)
        print("INFO: Extrayendo coordinadores desde MySQL (tblSecres)...")
        mysql_cursor.execute("SELECT Id, Id_Facultad, IdCarrera, UserLevel, Estado, FechReg FROM tblSecres")
        coordinadores_mysql = mysql_cursor.fetchall()
        print(f"INFO: Se extrajeron {len(coordinadores_mysql)} registros de coordinadores.")

        # 4. Procesar y transformar los datos
        registros_para_insertar = []
        
        for coord in coordinadores_mysql:
            id_coordinador = coord['Id']
            id_facultad = coord['Id_Facultad']
            id_carrera_mysql = coord['IdCarrera']
            nivel = coord['UserLevel']
            estado = coord['Estado']
            fecha = coord['FechReg']

            # CASO 1: El coordinador tiene una carrera específica (IdCarrera != 0)
            if id_carrera_mysql != 0:
                registros_para_insertar.append((
                    id_coordinador, nivel, id_facultad, id_carrera_mysql, fecha, estado
                ))
            # CASO 2: El coordinador es de facultad (IdCarrera == 0)
            else:
                carreras_a_asignar = carreras_por_facultad.get(id_facultad, [])
                if not carreras_a_asignar:
                    print(f"ADVERTENCIA: El coordinador {id_coordinador} de la facultad {id_facultad} no tiene carreras para asignar.")
                    continue
                
                for id_carrera_pg in carreras_a_asignar:
                    registros_para_insertar.append((
                        id_coordinador, nivel, id_facultad, id_carrera_pg, fecha, estado
                    ))
        
        print(f"INFO: Se generaron {len(registros_para_insertar)} registros para insertar en PostgreSQL.")

        # 5. Inserción masiva en PostgreSQL
        if registros_para_insertar:
            # Limpiar la tabla de destino antes de insertar
            print("INFO: Limpiando la tabla public.tbl_coordinador_carrera...")
            pg_cursor.execute("TRUNCATE TABLE public.tbl_coordinador_carrera RESTART IDENTITY;")

            print("INFO: Iniciando carga masiva de datos...")
            insert_query = """
                INSERT INTO public.tbl_coordinador_carrera (
                    id_coordinador, nivel_coordinador, id_facultad, 
                    id_carrera, fecha, estado
                ) VALUES %s;
            """
            execute_values(pg_cursor, insert_query, registros_para_insertar)
            
            pg_conn.commit()
            print(f"¡Éxito! Se han insertado {len(registros_para_insertar)} registros en tbl_coordinador_carrera.")
        else:
            print("INFO: No hay registros para insertar.")

    except Exception as e:
        print(f"ERROR: Ocurrió un error durante la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()
        if mysql_cursor:
            mysql_cursor.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Fin de la migración de TBL_COORDINADOR_CARRERA ---")

if __name__ == '__main__':
    migrar_tbl_coordinador_carrera()
