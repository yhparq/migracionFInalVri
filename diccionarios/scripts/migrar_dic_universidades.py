import sys
import os
import io
import csv

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrate_dic_universidades_from_csv():
    """
    Migra datos desde un CSV, corrigiendo los valores booleanos ("true"/"false")
    a enteros (1/0) antes de cargarlos en la tabla dic_universidades.
    """
    print("--- Iniciando migración de Universidades desde CSV ---")
    
    pg_conn = None
    
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'dic_universidades_rows.csv')

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
                # row[0]: id, row[1]: nombre, row[2]: abreviatura, row[3]: estado, ...
                # Convertir el estado de 'true'/'false' a 1/0
                estado = 1 if row[3].lower() == 'true' else 0
                
                # Reconstruir la fila con el estado corregido
                transformed_data.append(
                    (row[0], row[1], row[2], estado, row[4], row[5], row[6])
                )

        if not transformed_data:
            print("No hay datos para migrar.")
            return

        # 2. Usar COPY desde el buffer en memoria
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter='\t', quotechar='"')
        writer.writerows(transformed_data)
        buffer.seek(0)

        columns = ('id', 'nombre', 'abreviatura', 'estado_dic_universidades', 'pais', 'tipo_institucion', 'tipo_gestion')
        sql_copy = f"COPY public.dic_universidades ({', '.join(columns)}) FROM STDIN WITH CSV DELIMITER AS E'\t'"
        
        print("Iniciando carga masiva con COPY en PostgreSQL...")
        pg_cursor.copy_expert(sql=sql_copy, file=buffer)

        pg_conn.commit()
        
        print(f"¡Éxito! Se han cargado {len(transformed_data)} registros en 'dic_universidades' usando COPY.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()
        print("--- Migración de Universidades finalizada ---")

if __name__ == '__main__':
    migrate_dic_universidades_from_csv()