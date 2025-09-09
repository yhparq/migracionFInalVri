import sys
import os
import io

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def migrar_dic_nivel_coordinador():
    """
    Populates the dic_nivel_coordinador table from a CSV file using COPY.
    """
    conn = None
    try:
        conn = get_postgres_connection()
        cur = conn.cursor()

        # Path to the CSV file
        csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'dic_nivel_coordinador_rows.csv')

        with open(csv_file_path, 'r') as f:
            # Use copy_expert to COPY from STDIN
            cur.copy_expert("COPY dic_nivel_coordinador FROM STDIN WITH CSV HEADER", f)

        conn.commit()
        print("Successfully populated dic_nivel_coordinador.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrar_dic_nivel_coordinador()
