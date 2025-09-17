import sys
import os
import csv
import psycopg2

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrate_dic_nivel_admins_from_csv():
    """
    Reads data from dic_nivel_admins_rows.csv and inserts it into the dic_nivel_admins table in PostgreSQL using COPY.
    """
    print("--- Iniciando migración de Nivel de Administradores desde CSV ---")
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()

        # Path to the CSV file
        csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'dic_nivel_admins_rows.csv')

        if not os.path.exists(csv_file_path):
            print(f"Error: El archivo CSV no se encuentra en la ruta: {csv_file_path}")
            return

        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            f.seek(0)

            # Construir la sentencia COPY dinámicamente
            sql = f"""
                COPY public.dic_nivel_admins ({', '.join(header)})
                FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');
            """
            print(f"Ejecutando: COPY public.dic_nivel_admins ({', '.join(header)})...")
            cur.copy_expert(sql, f)

        conn.commit()
        print("¡Éxito! Se han cargado los datos en 'dic_nivel_admins' usando COPY.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
        print("--- Migración de Nivel de Administradores finalizada ---")

if __name__ == "__main__":
    migrate_dic_nivel_admins_from_csv()