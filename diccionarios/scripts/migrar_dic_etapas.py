import sys
import os
import io
import csv

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrate_dic_etapas_from_csv():
    """
    Migra datos desde un archivo CSV (dic_etapas_rows.csv) a la tabla
    dic_etapas en PostgreSQL usando el método de carga masiva COPY.
    """
    print("--- Iniciando migración de Etapas desde CSV ---")
    
    pg_conn = None
    
    # Ruta al archivo CSV de origen
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'dic_etapas_rows.csv')

    if not os.path.exists(csv_file_path):
        print(f"Error: El archivo CSV no se encuentra en la ruta: {csv_file_path}")
        return

    try:
        # 1. Establecer conexión a PostgreSQL
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("No se pudo establecer la conexión a PostgreSQL.")

        pg_cursor = pg_conn.cursor()

        # 2. Leer el archivo CSV y cargarlo en un buffer en memoria
        print(f"Leyendo archivo CSV: {csv_file_path}")
        
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            # Usamos copy_expert para leer directamente del archivo
            # Esto es extremadamente eficiente para archivos grandes
            
            # Omitimos la cabecera del CSV con HEADER
            columns = ('id', 'nombre', 'descripcion')
            sql_copy = f"COPY public.dic_etapas ({', '.join(columns)}) FROM STDIN WITH CSV HEADER DELIMITER ','"
            
            print("Iniciando carga masiva con COPY en PostgreSQL...")
            pg_cursor.copy_expert(sql=sql_copy, file=f)

        # 3. Confirmar la transacción
        pg_conn.commit()
        
        # copy_expert no actualiza rowcount, así que no podemos verificar el número de filas insertadas directamente.
        print("¡Éxito! Se han cargado los datos en 'dic_etapas' usando COPY.")

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
        print("--- Migración de Etapas finalizada ---")

if __name__ == '__main__':
    migrate_dic_etapas_from_csv()
