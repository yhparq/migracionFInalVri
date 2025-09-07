import psycopg2
import sys
import os
from db_connections import get_postgres_connection

def create_system_user():
    """
    Asegura que el usuario de sistema ('sistema@vriunap.pe') exista en la base de datos.
    Si no existe, lo crea. Si ya existe, no hace nada.
    """
    print("--- Verificando/Creando usuario del sistema ---")
    pg_conn = None
    try:
        pg_conn = get_postgres_connection()
        if pg_conn is None:
            raise Exception("No se pudo conectar a la base de datos de PostgreSQL.")

        pg_cur = pg_conn.cursor()

        # ON CONFLICT (correo) DO NOTHING es la forma más segura y eficiente de manejar esto.
        # Si el correo ya existe, el comando simplemente no hace nada.
        insert_query = """
            INSERT INTO public.tbl_usuarios 
            (nombres, apellidos, num_doc_identidad, correo, estado) 
            VALUES ('Sistema', 'VRI', '00000000', 'sistema@vriunap.pe', 1)
            ON CONFLICT (correo) DO NOTHING;
        """
        
        pg_cur.execute(insert_query)
        
        # Verificar si se insertó una fila o si ya existía
        if pg_cur.rowcount > 0:
            print("  Usuario 'sistema@vriunap.pe' creado con éxito.")
        else:
            print("  El usuario 'sistema@vriunap.pe' ya existía.")
            
        pg_conn.commit()

    except Exception as e:
        print(f"  ERROR CRÍTICO: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
            print("--- Conexión cerrada ---")

if __name__ == '__main__':
    create_system_user()
