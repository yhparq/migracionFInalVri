import sys
import os
import io
import csv
import psycopg2

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrate_tbl_estructura_academica_from_csv():
    """
    Migra datos desde un CSV a la tabla tbl_estructura_academica en PostgreSQL
    utilizando el método de carga masiva COPY.
    """
    print("--- Iniciando migración de Estructura Académica desde CSV ---")
    
    pg_conn = None
    
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'tbl_estructura_academica_rows.csv')

    if not os.path.exists(csv_file_path):
        print(f"Error: El archivo CSV no se encuentra en la ruta: {csv_file_path}")
        return

    try:
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("No se pudo establecer la conexión a PostgreSQL.")

        pg_cursor = pg_conn.cursor()

        # 1. Leer el CSV y cargarlo en un buffer, seleccionando solo las columnas necesarias
        print(f"Leyendo y transformando datos desde: {csv_file_path}")
        
        transformed_data = []
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Omitir la cabecera
            for row in reader:
                # CSV: id,nombre,id_carrera,id_facultad,id_especialidad,id_sede,estado_ea
                # Seleccionamos: id, nombre, id_especialidad, id_sede, estado_ea
                transformed_data.append((row[0], row[1], row[4], row[5], row[6]))

        if not transformed_data:
            print("No hay datos para migrar.")
            return

        # 2. Usar COPY desde el buffer en memoria
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter='\t', quotechar='"')
        writer.writerows(transformed_data)
        buffer.seek(0)

        columns = ('id', 'nombre', 'id_especialidad', 'id_sede', 'estado_ea')
        sql_copy = f"COPY public.tbl_estructura_academica ({', '.join(columns)}) FROM STDIN WITH CSV DELIMITER AS E'\t'"
        
        print("Iniciando carga masiva con COPY en PostgreSQL...")
        pg_cursor.copy_expert(sql=sql_copy, file=buffer)

        pg_conn.commit()
        
        print(f"¡Éxito! Se han cargado {len(transformed_data)} registros en 'tbl_estructura_academica'.")

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
