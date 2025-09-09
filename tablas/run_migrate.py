import sys
import os
import psycopg2

# Añadir el directorio 'scripts' y el raíz al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_connections import get_postgres_connection
from migrar_usuarios_y_docentes import migrate_usuarios_y_docentes_fast
from migrar_tbl_estructura_academica import migrate_tbl_estructura_academica_from_csv
from migrar_usuarios_y_tesistas import migrate_usuarios_y_tesistas_fast_v2
from migrar_tbl_sublineas_vri import migrate_tbl_sublineas_vri_fast
from migrar_tbl_tramites import migrate_tbl_tramites_fast
from migrar_tbl_docente_categoria_historial import migrate_docente_categoria_historial_mapeado
from migrar_tbl_asignacion_jurado import migrate_tbl_asignacion_jurado_fast
from crear_usuario_sistema import create_system_user
from migrar_tbl_conformacion_jurado import migrate_tbl_conformacion_jurado_fast
from migrar_tbl_correcciones import migrate_tbl_correcciones_jurados
from migrar_tbl_tramites_det import migrate_tbl_tramites_det
from migrar_tbl_dictamenes_info import migrate_tbl_dictamenes_info
from migrar_tbl_docentes_lineas import migrate_tbl_docentes_lineas
from migrar_tbl_docentes_lineas_historial import migrate_tbl_docentes_lineas_historial
from migrar_tbl_dictamenes_sustentaciones   import migrate_tbl_dictamenes_sustentaciones
from migrar_tbl_admins import migrar_tbl_admins
from migrar_tbl_coordinadores import migrar_tbl_coordinadores
from migrar_tbl_coordinador_carrera import migrar_tbl_coordinador_carrera

def clean_transactional_tables():
    """
    CORREGIDO v6: Limpia dinámicamente SOLO las tablas transaccionales ('tbl_*')
    ejecutando un TRUNCATE por cada tabla para mayor robustez.
    """
    print("--- Iniciando limpieza de tablas transaccionales ('tbl_*') ---")
    
    pg_conn = None
    try:
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("No se pudo conectar a PostgreSQL.")
        
        with pg_conn.cursor() as cursor:
            # 1. Obtener todos los nombres de tablas que empiezan con 'tbl_'
            print("  Obteniendo lista de tablas 'tbl_*'...")
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name LIKE 'tbl_%';
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                print("  No se encontraron tablas 'tbl_*' para limpiar.")
                return

            # 2. Iterar y truncar cada tabla individualmente
            print(f"  Se encontraron {len(tables)} tablas para limpiar. Procediendo...")
            for table_name in tables:
                try:
                    # Consulta TRUNCATE formateada correctamente
                    truncate_query = f'TRUNCATE TABLE public."{table_name}" RESTART IDENTITY CASCADE;'
                    cursor.execute(truncate_query)
                except psycopg2.Error as table_error:
                    print(f"    - ADVERTENCIA: No se pudo limpiar la tabla '{table_name}'. Error: {table_error}")
                    pg_conn.rollback()

            pg_conn.commit()
            print("--- Limpieza de tablas transaccionales completada. ---")

    except Exception as e:
        print(f"Error durante el proceso de limpieza de las tablas: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()

def main():
    """
    Orquesta la limpieza y ejecución de los scripts de migración para las tablas transaccionales.
    """
    print("--- INICIANDO PROCESO DE MIGRACIÓN DE TABLAS ---")
    
    # 1. Limpiar las tablas transaccionales antes de empezar
    clean_transactional_tables()
    
    # 2. Ejecutar migraciones de tablas en el orden correcto
    print("\n--- Ejecutando scripts de migración de tablas ---")
    
    migrate_tbl_estructura_academica_from_csv()
    migrate_usuarios_y_docentes_fast()
    migrate_tbl_sublineas_vri_fast()
    migrate_usuarios_y_tesistas_fast_v2()
    migrate_tbl_tramites_fast()
    migrate_docente_categoria_historial_mapeado()
    create_system_user()
    # migrate_tbl_asignacion_jurado_fast()
    # migrate_tbl_conformacion_jurado_fast()
    # migrate_tbl_correcciones_jurados()
    # migrate_tbl_tramites_det()
    # migrate_tbl_docentes_lineas()
    # migrate_tbl_docentes_lineas_historial()
    # migrate_tbl_dictamenes_info()
    # migrate_tbl_dictamenes_sustentaciones()
    # migrar_tbl_admins()
    migrar_tbl_coordinadores()
    # migrar_tbl_coordinador_carrera()

    
    print("\n--- PROCESO DE MIGRACIÓN DE TABLAS FINALIZADO ---")

if __name__ == '__main__':
    main()
