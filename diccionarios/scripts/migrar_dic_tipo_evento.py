import sys
import os
import io
import csv

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrate_dic_tipo_evento_from_csv():
    """
    Migra datos desde un archivo CSV (dic_tipo_evento_rows.csv) a la tabla
    dic_tipo_evento en PostgreSQL usando el método de carga masiva COPY.
    El script lee la cabecera del CSV para construir dinámicamente la sentencia COPY,
    haciéndolo robusto a la ausencia de columnas como 'descripcion'.
    """
    print("--- Iniciando migración de Tipo Evento desde CSV ---")
    
    pg_conn = None
    
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'dic_tipo_evento_rows.csv')

    if not os.path.exists(csv_file_path):
        print(f"Error: El archivo CSV no se encuentra en la ruta: {csv_file_path}")
        return

    try:
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("No se pudo establecer la conexión a PostgreSQL.")

        pg_cursor = pg_conn.cursor()

        print(f"Leyendo archivo CSV: {csv_file_path}")
        
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            # Leer la cabecera del CSV para obtener las columnas
            reader = csv.reader(f)
            header = next(reader)
            f.seek(0)  # Volver al inicio del archivo para que copy_expert lo lea completo

            # Construir la sentencia COPY dinámicamente
            sql_copy = f"COPY public.dic_tipo_evento ({', '.join(header)}) FROM STDIN WITH CSV HEADER DELIMITER ','"
            
            print(f"Ejecutando: COPY public.dic_tipo_evento ({', '.join(header)})...")
            pg_cursor.copy_expert(sql=sql_copy, file=f)

        pg_conn.commit()
        
        print("¡Éxito! Se han cargado los datos en 'dic_tipo_evento' usando COPY.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()
        print("--- Migración de Tipo Evento finalizada ---")

if __name__ == '__main__':
    migrate_dic_tipo_evento_from_csv()