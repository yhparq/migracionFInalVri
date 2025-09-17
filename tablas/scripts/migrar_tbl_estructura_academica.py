import sys
import os
import psycopg2

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrate_tbl_estructura_academica_from_csv():
    """
    Migra datos desde un CSV a la tabla tbl_estructura_academica en PostgreSQL
    utilizando el método de carga masiva COPY de forma directa.
    """
    print("--- Iniciando migración de Estructura Académica desde CSV ---")
    
    pg_conn = None
    pg_cursor = None
    
    # Ruta directa al archivo CSV original
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'tbl_estructura_academica_rows.csv')

    if not os.path.exists(csv_file_path):
        print(f"Error: El archivo CSV no se encuentra en la ruta: {csv_file_path}")
        return

    try:
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("No se pudo establecer la conexión a PostgreSQL.")

        pg_cursor = pg_conn.cursor()

        # SQL para COPY. Asume que el orden de columnas en el CSV es:
        # id,nombre,id_carrera,id_facultad,id_especialidad,id_sede,estado_ea
        # y que la tabla tbl_estructura_academica tiene estas columnas.
        sql_copy = """
            COPY public.tbl_estructura_academica(id, nombre, id_carrera, id_facultad, id_especialidad, id_sede, estado_ea)
            FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');
        """
        
        print("Iniciando carga masiva con COPY desde el archivo CSV...")
        
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            pg_cursor.copy_expert(sql=sql_copy, file=f)

        # Contar las filas insertadas para confirmación
        row_count = pg_cursor.rowcount
        pg_conn.commit()
        
        print(f"¡Éxito! Se han cargado {row_count} registros en 'tbl_estructura_academica'.")

    except (Exception, psycopg2.Error) as e:
        print(f"Ocurrió un error: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()
        print("--- Migración de Estructura Académica finalizada ---")

if __name__ == '__main__':
    migrate_tbl_estructura_academica_from_csv()