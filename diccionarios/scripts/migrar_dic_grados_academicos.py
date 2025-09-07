import sys
import os
import io
import csv

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrate_dic_grados_academicos_from_csv():
    """
    Migra datos desde un CSV sin ID a la tabla dic_grados_academicos,
    dejando que el ID sea autogenerado y estableciendo un estado por defecto.
    """
    print("--- Iniciando migración de Grados Académicos desde CSV ---")
    
    pg_conn = None
    
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'dic_grados_academicos_rows.csv')

    if not os.path.exists(csv_file_path):
        print(f"Error: El archivo CSV no se encuentra en la ruta: {csv_file_path}")
        return

    try:
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("No se pudo establecer la conexión a PostgreSQL.")

        pg_cursor = pg_conn.cursor()

        # 1. Leer el CSV y transformar los datos en memoria
        print(f"Leyendo y transformando datos desde: {csv_file_path}")
        
        transformed_data = []
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Omitir la cabecera
            for row in reader:
                # row[0] = nombre, row[1] = abreviatura
                # Añadimos el estado por defecto '1'
                transformed_data.append((row[0], row[1], 1))

        if not transformed_data:
            print("No hay datos para migrar.")
            return

        # 2. Usar COPY desde el buffer en memoria
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter='\t', quotechar='"')
        writer.writerows(transformed_data)
        buffer.seek(0)

        # Especificamos las columnas que vamos a insertar, omitiendo 'id'
        columns = ('nombre', 'abreviatura', 'estado_dic_grados_academicos')
        sql_copy = f"COPY public.dic_grados_academicos ({', '.join(columns)}) FROM STDIN WITH CSV DELIMITER AS E'\t'"
        
        print("Iniciando carga masiva con COPY en PostgreSQL...")
        pg_cursor.copy_expert(sql=sql_copy, file=buffer)

        # 3. Confirmar la transacción
        pg_conn.commit()
        
        print(f"¡Éxito! Se han cargado {len(transformed_data)} registros en 'dic_grados_academicos'.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        # 4. Cerrar conexiones
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()
        print("--- Migración de Grados Académicos finalizada ---")

if __name__ == '__main__':
    migrate_dic_grados_academicos_from_csv()