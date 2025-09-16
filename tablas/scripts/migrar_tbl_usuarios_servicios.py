import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrar_tbl_usuarios_servicios():
    """
    Populates the tbl_usuarios_servicios table by assigning a specific service (role)
    to each user based on their presence in the docentes, tesistas, coordinadores,
    and admins tables.
    """
    pg_conn = None
    try:
        pg_conn = get_postgres_connection()
        pg_cur = pg_conn.cursor()

        print("--- Iniciando la migración de roles de usuario (tbl_usuarios_servicios) ---")

        # 1. Limpiar la tabla para asegurar una carga limpia
        print("INFO: Limpiando la tabla tbl_usuarios_servicios y sus dependencias (CASCADE)...")
        pg_cur.execute("TRUNCATE TABLE public.tbl_usuarios_servicios RESTART IDENTITY CASCADE;")

        # 2. Definir las reglas de inserción
        # (id_servicio, tabla_origen, nombre_rol)
        roles_a_migrar = [
            (1, 'tbl_tesistas', 'Tesistas'),
            (2, 'tbl_docentes', 'Docentes'),
            (3, 'tbl_coordinadores', 'Coordinadores'),
            (4, 'tbl_admins', 'Administradores'),
            (5, 'tbl_coasesores', 'Coasesores')
        ]

        total_inserted = 0

        # 3. Ejecutar la inserción para cada rol
        for id_servicio, tabla_origen, nombre_rol in roles_a_migrar:
            print(f"INFO: Asignando rol de '{nombre_rol}' (Servicio ID: {id_servicio}) a usuarios desde '{tabla_origen}'...")
            
            insert_query = ""
            if tabla_origen == 'tbl_coasesores':
                # Consulta especial para coasesores con JOIN para obtener el id_usuario
                insert_query = f"""
                    INSERT INTO public.tbl_usuarios_servicios (id_usuario, id_servicio, fecha_asignacion, estado)
                    SELECT
                        pi.id_usuario,
                        %s AS id_servicio,
                        NOW() AS fecha_asignacion,
                        1 AS estado
                    FROM
                        public.tbl_coasesores c
                    JOIN
                        public.tbl_perfil_investigador pi ON c.id_investigador = pi.id
                    ON CONFLICT (id_usuario, id_servicio) DO NOTHING;
                """
            else:
                # Consulta estándar para las demás tablas
                insert_query = f"""
                    INSERT INTO public.tbl_usuarios_servicios (id_usuario, id_servicio, fecha_asignacion, estado)
                    SELECT
                        t.id_usuario,
                        %s AS id_servicio,
                        NOW() AS fecha_asignacion,
                        1 AS estado
                    FROM
                        public.{tabla_origen} t
                    ON CONFLICT (id_usuario, id_servicio) DO NOTHING;
                """
            
            pg_cur.execute(insert_query, (id_servicio,))
            count = pg_cur.rowcount
            total_inserted += count
            print(f"INFO: Se asignaron {count} roles de '{nombre_rol}'.")

        pg_conn.commit()
        print(f"\n--- Migración de tbl_usuarios_servicios completada. Total de roles asignados: {total_inserted} ---")

    except Exception as e:
        print(f"ERROR: Ocurrió un error crítico durante la migración de usuarios_servicios: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()

if __name__ == "__main__":
    migrar_tbl_usuarios_servicios()
