
import sys
import os

# Añadir el directorio 'scripts' al sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# Añadir el directorio raíz para db_connections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_connections import get_postgres_connection
from migrar_dic_areas_ocde import migrate_dic_areas_ocde_fast
from migrar_dic_subareas_ocde import migrate_dic_subareas_ocde_fast
from migrar_dic_disciplinas import migrate_dic_disciplinas_fast
from migrar_dic_facultades import migrate_dic_facultades_fast
from migrar_dic_carreras import migrate_dic_carreras_fast
from migrar_dic_categoria import migrate_dic_categoria_fast
from migrar_dic_etapas import migrate_dic_etapas_from_csv
from migrar_dic_grados_academicos import migrate_dic_grados_academicos_from_csv
from migrar_dic_universidades import migrate_dic_universidades_from_csv
from migrar_dic_modalidades import migrate_dic_modalidades_from_csv
from migrar_dic_lineas_universidad import migrate_dic_lineas_universidad_fast
from migrar_dic_obtencion_studios import migrate_dic_obtencion_studios_from_csv
from migrar_dic_orden_jurado import migrate_dic_orden_jurado_from_csv
from migrar_dic_sedes import migrate_dic_sedes_from_csv
from migrar_dic_servicios import migrate_dic_servicios_from_csv
from migrar_dic_tipo_trabajos import migrate_dic_tipo_trabajos_from_csv
from migrar_dic_tipo_archivo import migrate_dic_tipo_archivo_from_csv
from scripts.migrar_dic_tipo_evento import migrate_dic_tipo_evento_from_csv
from migrar_dic_especialidades import migrate_dic_especialidades_from_csv
from migrar_dic_denominaciones import migrate_dic_denominaciones_from_csv
from migrar_dic_acciones import migrate_dic_acciones_from_csv
from migrar_dic_visto_bueno import migrate_dic_visto_bueno_from_csv
from migrar_dic_nivel_admins import migrate_dic_nivel_admins_from_csv
from migrar_dic_nivel_coordinador import migrar_dic_nivel_coordinador

def clean_database_tables():
    """
    Limpia dinámicamente todas las tablas 'dic_*' y 'tbl_*' en la base de datos.
    """
    print("--- Iniciando limpieza dinámica de la base de datos ---")
    
    pg_conn = None
    try:
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("No se pudo conectar a PostgreSQL.")
        
        with pg_conn.cursor() as cursor:
            # 1. Obtener todos los nombres de tablas de los esquemas 'public'
            print("Obteniendo lista de tablas 'dic_*' y 'tbl_*'...")
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND (table_name LIKE 'dic_%' OR table_name LIKE 'tbl_%');
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                print("No se encontraron tablas 'dic_*' o 'tbl_*' para limpiar.")
                return

            # 2. Construir y ejecutar la sentencia TRUNCATE
            # Usamos format() de forma segura porque los nombres de tabla vienen de la DB
            truncate_query = "TRUNCATE TABLE {} RESTART IDENTITY CASCADE;".format(
                ', '.join(f'public.\"{table}\"' for table in tables)
            )
            
            print("Ejecutando TRUNCATE en todas las tablas encontradas...")
            cursor.execute(truncate_query)
            
            pg_conn.commit()
            print(f"--- Limpieza completada. {len(tables)} tablas truncadas. ---")

    except Exception as e:
        print(f"Error durante la limpieza de la base de datos: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()

def main():
    """
    Orquesta la limpieza y ejecución de todos los scripts de migración.
    """
    print("--- INICIANDO PROCESO DE MIGRACIÓN GENERAL ---")
    
    # 1. Limpiar la base de datos antes de empezar
    clean_database_tables()
    
    # 2. Ejecutar migraciones en el orden correcto
    print("\n--- Ejecutando scripts de migración ---")
    
    # --- Nivel 0: Diccionarios sin dependencias ---
    migrate_dic_areas_ocde_fast()
    migrate_dic_subareas_ocde_fast()
    migrate_dic_disciplinas_fast()
    migrate_dic_facultades_fast()
    migrate_dic_carreras_fast()
    migrate_dic_categoria_fast()
    migrate_dic_etapas_from_csv()
    migrate_dic_grados_academicos_from_csv()
    # migrate_dic_universidades_from_csv()
    migrate_dic_modalidades_from_csv()
    migrate_dic_lineas_universidad_fast()
    migrate_dic_obtencion_studios_from_csv()
    migrate_dic_orden_jurado_from_csv()
    migrate_dic_sedes_from_csv()
    migrate_dic_servicios_from_csv()
    migrate_dic_tipo_trabajos_from_csv()
    migrate_dic_tipo_archivo_from_csv()
    migrate_dic_tipo_evento_from_csv()
    migrate_dic_especialidades_from_csv()
    migrate_dic_denominaciones_from_csv()
    migrate_dic_acciones_from_csv()
    migrate_dic_visto_bueno_from_csv()
    migrate_dic_nivel_admins_from_csv()
    migrar_dic_nivel_coordinador()
    
    # (Aquí se llamarán las demás migraciones)
    
    print("\n--- PROCESO DE MIGRACIÓN GENERAL FINALIZADO ---")

if __name__ == '__main__':
    main()
