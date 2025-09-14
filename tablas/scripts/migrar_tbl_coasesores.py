
import os
import sys
import psycopg2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection

def migrate_coasesores():
    """
    Migrates all users from tbl_perfil_investigador to tbl_coasesores with estado_coasesor = 1.
    """
    pg_conn = None
    print("--- Iniciando migración de perfiles a co-asesores ---")

    try:
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("Database connection failed.")

        pg_cursor = pg_conn.cursor()

        # Get all investigator IDs from tbl_perfil_investigador
        pg_cursor.execute("SELECT id FROM tbl_perfil_investigador;")
        investigator_ids = pg_cursor.fetchall()

        if not investigator_ids:
            print("INFO: No hay investigadores en tbl_perfil_investigador para migrar.")
            return

        coasesores_to_insert = [(row[0], 1) for row in investigator_ids]

        print(f"--- Insertando/Actualizando {len(coasesores_to_insert)} co-asesores ---")

        insert_query = """
            INSERT INTO tbl_coasesores (id_investigador, estado_coasesor)
            VALUES (%s, %s)
            ON CONFLICT (id_investigador) DO UPDATE SET
                estado_coasesor = EXCLUDED.estado_coasesor;
        """
        pg_cursor.executemany(insert_query, coasesores_to_insert)
        pg_conn.commit()

        print(f"--- Migración de co-asesores completada. Se procesaron {pg_cursor.rowcount} registros. ---")

    except (Exception, psycopg2.Error) as e:
        print(f"ERROR: Ocurrió un error durante la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        print("INFO: Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    migrate_coasesores()
