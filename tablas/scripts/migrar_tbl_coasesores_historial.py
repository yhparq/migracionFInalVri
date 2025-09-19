import sys
import os
from datetime import timedelta, datetime
from collections import defaultdict

# Añadir el directorio raíz al sys.path para poder importar db_connections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection, get_mysql_absmain_connection
from psycopg2.extras import execute_values

def migrar_tbl_coasesores_historial():
    """
    Puebla la tabla tbl_coasesores_historial basándose en los datos de
    tbl_coasesores (PostgreSQL) y tblDocAsesors (MySQL).
    La lógica de historial se basa en el estado del coasesor:
    - estado 0 (Registrado): Crea 1 registro de historial.
    - estado 1 (Aceptado): Crea 2 registros (registrado -> aceptado).
    - estado 2 (Rechazado): Crea 2 registros (registrado -> rechazado).
    """
    print("--- Iniciando migración de TBL_COASESORES_HISTORIAL (Lógica Corregida) ---")
    
    pg_conn = None
    mysql_conn = None
    
    try:
        # 1. Conexión a las bases de datos
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_absmain_connection()
        
        if not pg_conn or not mysql_conn:
            raise Exception("No se pudieron establecer las conexiones a las bases de datos.")
            
        pg_cursor = pg_conn.cursor()
        mysql_cursor = mysql_conn.cursor(dictionary=True)

        # 2. Obtener IDs de las acciones relevantes desde PostgreSQL
        print("INFO: Obteniendo IDs de acciones para el historial...")
        pg_cursor.execute("""
            SELECT nombre, id FROM public.dic_acciones 
            WHERE nombre IN ('coasesor registrado', 'coasesor aceptado', 'coasesor rechazado')
        """)
        acciones = dict(pg_cursor.fetchall())
        
        id_accion_registrado = acciones.get('coasesor registrado')
        id_accion_aceptado = acciones.get('coasesor aceptado')
        id_accion_rechazado = acciones.get('coasesor rechazado')
        
        if not all([id_accion_registrado, id_accion_aceptado, id_accion_rechazado]):
            raise Exception("No se encontraron todas las acciones requeridas ('registrado', 'aceptado', 'rechazado') en dic_acciones.")
        
        print(f"INFO: IDs de acciones -> Registrado: {id_accion_registrado}, Aceptado: {id_accion_aceptado}, Rechazado: {id_accion_rechazado}")

        # 3. Obtener fechas de registro originales desde MySQL
        print("INFO: Extrayendo fechas de registro desde MySQL (tblDocAsesors)...")
        mysql_cursor.execute("SELECT IdPilar, FechaReg FROM tblDocAsesors")
        fechas_registro_map = {asesor['IdPilar']: asesor['FechaReg'] for asesor in mysql_cursor.fetchall()}
        print(f"INFO: Se obtuvieron {len(fechas_registro_map)} fechas de registro.")

        # 4. Obtener los coasesores actuales desde PostgreSQL
        print("INFO: Obteniendo coasesores desde PostgreSQL (tbl_coasesores)...")
        pg_cursor.execute("SELECT id, id_investigador, estado_coasesor FROM public.tbl_coasesores")
        coasesores_pg = pg_cursor.fetchall()
        print(f"INFO: Se encontraron {len(coasesores_pg)} coasesores para procesar.")

        # 5. Procesar y generar los registros del historial
        registros_historial = []
        id_usuario_sistema = 27271 # ID fijo para el usuario verificador (sistema)

        for id_coasesor, id_investigador, estado in coasesores_pg:
            fecha_registro = fechas_registro_map.get(id_investigador) or datetime.now()
            if not fechas_registro_map.get(id_investigador):
                print(f"ADVERTENCIA: No se encontró fecha para el coasesor con id_investigador {id_investigador}. Se usará la fecha actual.")

            # Siempre se crea el evento de "registrado" primero
            registros_historial.append((
                id_coasesor, fecha_registro, id_usuario_sistema, None, 0, id_accion_registrado
            ))

            # Si está aceptado, se añade el segundo evento
            if estado == 1:
                registros_historial.append((
                    id_coasesor, fecha_registro + timedelta(seconds=1), id_usuario_sistema, None, 1, id_accion_aceptado
                ))
            # Si está rechazado, se añade el segundo evento
            elif estado == 2:
                registros_historial.append((
                    id_coasesor, fecha_registro + timedelta(seconds=1), id_usuario_sistema, None, 2, id_accion_rechazado
                ))
        
        print(f"INFO: Se generaron {len(registros_historial)} registros para el historial.")

        # 6. Inserción masiva en PostgreSQL
        if registros_historial:
            print("INFO: Limpiando la tabla public.tbl_coasesores_historial...")
            pg_cursor.execute("TRUNCATE TABLE public.tbl_coasesores_historial RESTART IDENTITY;")

            print("INFO: Iniciando carga masiva de datos en el historial...")
            insert_query = """
                INSERT INTO public.tbl_coasesores_historial (
                    id_coasesor, fecha_cambio, id_usuario_verificador, 
                    detalle, estado_coasesor, id_accion
                ) VALUES %s;
            """
            execute_values(pg_cursor, insert_query, registros_historial)
            
            pg_conn.commit()
            print(f"¡Éxito! Se han insertado {len(registros_historial)} registros en tbl_coasesores_historial.")
        else:
            print("INFO: No hay registros de historial para insertar.")

    except Exception as e:
        print(f"ERROR: Ocurrió un error durante la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_cursor: pg_cursor.close()
        if pg_conn: pg_conn.close()
        if mysql_cursor: mysql_cursor.close()
        if mysql_conn: mysql_conn.close()
        print("--- Fin de la migración de TBL_COASESORES_HISTORIAL ---")

if __name__ == '__main__':
    migrar_tbl_coasesores_historial()
