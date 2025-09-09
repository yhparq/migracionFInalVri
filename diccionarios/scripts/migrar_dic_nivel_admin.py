import sys
import os
import psycopg2

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrar_dic_nivel_admin():
    """
    Reads data from dic_nivel_admin_rows.csv and inserts it into the dic_nivel_admin table in PostgreSQL using COPY.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()

        # Path to the CSV file
        csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'dic_nivel_admin_rows.csv')

        with open(csv_file_path, 'r') as f:
            # The COPY command is more suitable for bulk inserts.
            # We need to specify the columns since the CSV has a header.
            sql = """
                COPY dic_nivel_admin(id, nombre, descripcion, estado)
                FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',');
            """
            cur.copy_expert(sql, f)

        conn.commit()
        print("Successfully migrated dic_nivel_admin data using COPY.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrar_dic_nivel_admin()
