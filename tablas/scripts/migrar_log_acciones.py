import sys
import os
import re
from io import StringIO
from datetime import datetime

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def normalize_action_name(name):
    """Normaliza el nombre de una acción para facilitar el mapeo."""
    if not isinstance(name, str):
        return ''
    return ' '.join(name.strip().lower().split())

def sanitize_for_copy(value):
    """
    Sanitizes a value for the COPY command, correctly handling None as NULL.
    """
    if value is None:
        return r'\N'
    return str(value).replace('\\', '\\\\').replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')

def migrar_log_acciones():
    """
    Migrates data from logTramites (MySQL) to log_acciones (PostgreSQL),
    applying complex mapping logic and using a defined fallback action.
    """
    mysql_conn = None
    pg_conn = None
    try:
        mysql_conn = get_mysql_pilar3_connection()
        pg_conn = get_postgres_connection()
        pg_cur = pg_conn.cursor()

        print("--- Iniciando migración de log de acciones (log_acciones) ---")

        # 1. Cargar mapas de traducción y definir la acción de respaldo
        print("INFO: Cargando mapas de traducción desde PostgreSQL en memoria...")
        
        pg_cur.execute("SELECT id, nombre, id_etapa_pertenencia FROM dic_acciones")
        acciones_data = pg_cur.fetchall()
        mapa_acciones = {normalize_action_name(row[1]): (row[0], row[2]) for row in acciones_data}
        
        accion_default = next(( (row[0], row[2]) for row in acciones_data if row[0] == 49), None)
        if not accion_default:
            raise Exception("La acción por defecto con ID 49 ('Correcion de estado') no se encontró en dic_acciones.")
        print("INFO: Acción de respaldo configurada en ID 49.")

        pg_cur.execute("SELECT id_antiguo, id FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        mapa_tramites = dict(pg_cur.fetchall())

        pg_cur.execute("SELECT id, id_usuario FROM tbl_admins")
        mapa_admins = dict(pg_cur.fetchall())
        pg_cur.execute("SELECT id, id_usuario FROM tbl_docentes")
        mapa_docentes = dict(pg_cur.fetchall())
        pg_cur.execute("SELECT id, id_usuario FROM tbl_coordinadores")
        mapa_coordinadores = dict(pg_cur.fetchall())
        pg_cur.execute("SELECT id, id_usuario FROM tbl_tesistas")
        mapa_tesistas = dict(pg_cur.fetchall())

        # 2. Obtener registros de logTramites de MySQL
        mysql_cur = mysql_conn.cursor(dictionary=True)
        mysql_cur.execute("SELECT IdTramite, Accion, Detalle, IdUser, Tipo, Fecha FROM logTramites")
        logs_antiguos = mysql_cur.fetchall()
        print(f"INFO: Se encontraron {len(logs_antiguos)} registros en logTramites.")

        log_records_to_insert = []
        registros_omitidos = 0
        now_timestamp = datetime.now()

        # 3. Procesar cada registro del log
        for log in logs_antiguos:
            id_tramite_nuevo = mapa_tramites.get(log['IdTramite'])
            if not id_tramite_nuevo:
                registros_omitidos += 1
                continue

            id_usuario_nuevo = None
            id_user_antiguo = log['IdUser']

            # 1. Manejo especial para IdUser = 0
            if id_user_antiguo == 0:
                id_usuario_nuevo = mapa_admins.get(7) # Asignar al admin con id=7
                if not id_usuario_nuevo:
                    print(f"ADVERTENCIA: El admin de respaldo con id=7 no fue encontrado. Omitiendo log para trámite {id_tramite_nuevo}.")
            
            # 2. Lógica normal para otros usuarios
            else:
                tipo_usuario = log['Tipo']
                if tipo_usuario:
                    # 'A' (Admin) y 'P' (Admin) se mapean a administradores
                    if tipo_usuario.isdigit() or tipo_usuario in ('P', 'A'):
                        id_usuario_nuevo = mapa_admins.get(id_user_antiguo)
                    # 'D' (Docente) se mapea a docentes
                    elif tipo_usuario == 'D':
                        id_usuario_nuevo = mapa_docentes.get(id_user_antiguo)
                    elif tipo_usuario == 'C':
                        id_usuario_nuevo = mapa_coordinadores.get(id_user_antiguo)
                    elif tipo_usuario == 'T':
                        id_usuario_nuevo = mapa_tesistas.get(id_user_antiguo)
            
            if id_usuario_nuevo is None:
                registros_omitidos += 1
                continue

            nombre_accion_norm = normalize_action_name(log['Accion'])
            id_accion_nuevo, id_etapa_nueva = mapa_acciones.get(nombre_accion_norm, accion_default)
            
            fecha_a_insertar = log['Fecha'] if log['Fecha'] is not None else now_timestamp

            log_records_to_insert.append(
                (id_tramite_nuevo, id_accion_nuevo, id_etapa_nueva, id_usuario_nuevo, fecha_a_insertar, log['Detalle'] or 'Sin detalle.')
            )

        print(f"INFO: Procesamiento finalizado. {len(log_records_to_insert)} registros serán migrados. {registros_omitidos} registros fueron omitidos.")

        # 4. Inserción masiva
        if log_records_to_insert:
            print("INFO: Realizando inserción masiva en log_acciones...")
            pg_cur.execute("TRUNCATE TABLE public.log_acciones RESTART IDENTITY;")
            
            buffer = StringIO()
            for record in log_records_to_insert:
                sanitized_record = [sanitize_for_copy(field) for field in record]
                buffer.write('\t'.join(sanitized_record) + '\n')
            buffer.seek(0)
            
            pg_cur.copy_expert("COPY log_acciones(id_tramite, id_accion, id_etapa, id_usuario, fecha, mensaje) FROM STDIN", buffer)
            print(f"INFO: Se insertaron {pg_cur.rowcount} registros en log_acciones.")
        
        pg_conn.commit()
        print("\n--- Migración de log_acciones finalizada exitosamente. ---")

    except Exception as e:
        print(f"ERROR: Ocurrió un error crítico durante la migración de log_acciones: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if mysql_conn: mysql_conn.close()
        if pg_conn: pg_conn.close()

if __name__ == "__main__":
    migrar_log_acciones()
