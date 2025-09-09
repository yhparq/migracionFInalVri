import sys
import os
import pandas as pd
import io
from collections import defaultdict

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def sanitize_for_copy(value):
    """
    Sanitizes a value for the COPY command by removing newlines and tabs.
    """
    if value is None:
        return r'\N' # Represents NULL for PostgreSQL COPY
    
    # For dates, psycopg2/pandas might convert them to objects. Get the string representation.
    if hasattr(value, 'isoformat'):
        value = value.isoformat()
        
    clean_value = str(value).replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    return ' '.join(clean_value.split())

def migrar_tbl_coordinador_carrera():
    """
    Migrates coordinator-career relationships from MySQL's tblSecres
    to PostgreSQL's tbl_coordinador_carrera, handling the special
    case where IdCarrera = 0 means all careers in a faculty.
    """
    mysql_conn = None
    pg_conn = None
    
    try:
        print("\n--- Iniciando migración de Coordinador-Carrera ---")
        mysql_conn = get_mysql_pilar3_connection()
        pg_conn = get_postgres_connection()
        pg_cur = pg_conn.cursor()

        # 1. Get all existing careers from Postgres and map them by faculty
        print("Fetching career and faculty data from PostgreSQL...")
        pg_cur.execute("SELECT id, id_facultad FROM dic_carreras")
        carreras_por_facultad = defaultdict(list)
        for carrera_id, facultad_id in pg_cur.fetchall():
            if facultad_id:
                carreras_por_facultad[facultad_id].append(carrera_id)
        print(f"Found {len(carreras_por_facultad)} faculties with associated careers.")

        # 2. Fetch secretaries from MySQL
        print("Fetching coordinator data from MySQL (tblSecres)...")
        mysql_cur = mysql_conn.cursor(dictionary=True)
        mysql_cur.execute("SELECT Id, Id_Facultad, IdCarrera, UserLevel, Estado, FechReg FROM tblSecres")
        secretaries = mysql_cur.fetchall()
        print(f"Found {len(secretaries)} records in tblSecres.")

        records_to_insert = []

        # 3. Process each secretary record
        for sec in secretaries:
            id_coordinador = sec['Id']
            id_facultad = sec['Id_Facultad']
            id_carrera_mysql = sec['IdCarrera']
            
            # Rule: If IdCarrera is 0, assign all careers from the faculty
            if id_carrera_mysql == 0:
                if id_facultad in carreras_por_facultad:
                    carreras_a_asignar = carreras_por_facultad[id_facultad]
                    print(f"  -> Coordinator ID {id_coordinador} (Facultad {id_facultad}) gets {len(carreras_a_asignar)} careers.")
                    for carrera_id in carreras_a_asignar:
                        records_to_insert.append({
                            'id_coordinador': id_coordinador,
                            'nivel_coordinador': sec['UserLevel'],
                            'id_facultad': id_facultad,
                            'id_carrera': carrera_id,
                            'fecha': sec['FechReg'],
                            'estado': sec['Estado']
                        })
                else:
                    print(f"  -> WARNING: Coordinator ID {id_coordinador} has IdCarrera=0 but their faculty ({id_facultad}) has no careers mapped in PostgreSQL. Skipping.")
            
            # Rule: If IdCarrera is not 0, assign the specific career
            else:
                records_to_insert.append({
                    'id_coordinador': id_coordinador,
                    'nivel_coordinador': sec['UserLevel'],
                    'id_facultad': id_facultad,
                    'id_carrera': id_carrera_mysql,
                    'fecha': sec['FechReg'],
                    'estado': sec['Estado']
                })

        # 4. Use COPY for bulk insert after clearing the table
        if records_to_insert:
            print(f"\nPreparing {len(records_to_insert)} coordinator-career records for bulk insert...")
            
            # Truncate the table to ensure a clean migration run
            print("Clearing tbl_coordinador_carrera before insert...")
            pg_cur.execute("TRUNCATE TABLE tbl_coordinador_carrera RESTART IDENTITY;")

            csv_buffer = io.StringIO()
            for rec in records_to_insert:
                sanitized_values = [
                    sanitize_for_copy(rec['id_coordinador']),
                    sanitize_for_copy(rec['nivel_coordinador']),
                    sanitize_for_copy(rec['id_facultad']),
                    sanitize_for_copy(rec['id_carrera']),
                    sanitize_for_copy(rec['fecha']),
                    sanitize_for_copy(rec['estado'])
                ]
                csv_buffer.write('\t'.join(sanitized_values) + '\n')
            
            csv_buffer.seek(0)
            copy_sql = """
                COPY tbl_coordinador_carrera (id_coordinador, nivel_coordinador, id_facultad, id_carrera, fecha, estado) 
                FROM STDIN
            """
            pg_cur.copy_expert(sql=copy_sql, file=csv_buffer)
            
            print(f"Successfully inserted {len(records_to_insert)} records into tbl_coordinador_carrera.")

        pg_conn.commit()
        print("--- Migración de Coordinador-Carrera finalizada con éxito ---")

    except Exception as e:
        print(f"An error occurred: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if mysql_conn:
            mysql_conn.close()
        if pg_conn:
            pg_conn.close()

if __name__ == "__main__":
    migrar_tbl_coordinador_carrera()
