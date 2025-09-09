import sys
import os
import pandas as pd
import re
import io
import unicodedata

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def normalize_name(name):
    """
    Normalizes a name for robust matching by removing accents, prefixes,
    converting to lowercase, and standardizing whitespace.
    """
    if not isinstance(name, str):
        return ''
    
    # Remove accents (diacritics)
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove commas
    name = name.replace(',', '')
    
    # Remove prefixes
    name = re.sub(r'^(dr\.|dra\.|mg\.|msc\.|ing\.|lic\.|enf\.)\s*', '', name)
    
    # Standardize whitespace
    return ' '.join(name.split())

def clean_name_for_db(name):
    """
    A simpler cleaner for inserting names into the DB, preserving case.
    """
    if not isinstance(name, str):
        return ''
    name = re.sub(r'^(Dr\.|Dra\.|Mg\.|Msc\.|Ing\.|Lic\.|Enf\.)\s*', '', name, flags=re.IGNORECASE)
    return ' '.join(name.split())

def is_valid_dni(doc_id):
    """Checks if the document ID is a valid DNI (8 digits)."""
    return doc_id and doc_id.isdigit() and len(doc_id) == 8

def migrar_tbl_admins():
    """
    Migrates administrators from tblManagers, with robust, normalized name matching.
    """
    mysql_conn = None
    pg_conn = None
    try:
        mysql_conn = get_mysql_pilar3_connection()
        pg_conn = get_postgres_connection()
        pg_cur = pg_conn.cursor()

        # 1. Fetch existing users with robust concatenation and normalize them
        pg_cur.execute("SELECT id, num_doc_identidad, CONCAT_WS(' ', nombres, apellidos) as full_name FROM tbl_usuarios")
        existing_users_df = pd.DataFrame(pg_cur.fetchall(), columns=['id', 'num_doc_identidad', 'full_name'])
        existing_users_df['normalized_name'] = existing_users_df['full_name'].apply(normalize_name)
        
        users_by_dni = pd.Series(existing_users_df.id.values, index=existing_users_df.num_doc_identidad).to_dict()
        users_by_name = pd.Series(existing_users_df.id.values, index=existing_users_df.normalized_name).to_dict()

        # 2. Fetch managers from MySQL
        mysql_cur = mysql_conn.cursor(dictionary=True)
        mysql_cur.execute("SELECT Id, Usuario, Responsable, Nivel FROM tblManagers")
        managers = mysql_cur.fetchall()

        admin_records_to_insert = []
        special_status_names = {'JULIO', 'ROMEL', 'KHATERIN PAOLA', 'KELLY'}

        # 3. Process each manager
        for manager in managers:
            normalized_manager_name = normalize_name(manager['Responsable'])
            
            if is_valid_dni(manager['Usuario']):
                doc_id_to_use = manager['Usuario']
            else:
                doc_id_to_use = f"ADMIN_{manager['Id']}"

            id_usuario = None
            
            if doc_id_to_use in users_by_dni:
                id_usuario = users_by_dni[doc_id_to_use]
            elif normalized_manager_name in users_by_name:
                id_usuario = users_by_name[normalized_manager_name]
            else:
                cleaned_db_name = clean_name_for_db(manager['Responsable'])
                name_parts = cleaned_db_name.split()
                nombres = name_parts[0] if len(name_parts) > 0 else ''
                apellidos = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                placeholder_email = f"user.{doc_id_to_use}@migracion.vriunap.edu.pe"

                print(f"User not found for '{cleaned_db_name}' (Normalized: '{normalized_manager_name}'). Creating new user.")
                pg_cur.execute(
                    """
                    INSERT INTO tbl_usuarios (num_doc_identidad, nombres, apellidos, correo)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (num_doc_identidad) DO UPDATE SET nombres = EXCLUDED.nombres, apellidos = EXCLUDED.apellidos
                    RETURNING id;
                    """,
                    (doc_id_to_use, nombres, apellidos, placeholder_email)
                )
                id_usuario = pg_cur.fetchone()[0]
                
                users_by_dni[doc_id_to_use] = id_usuario
                users_by_name[normalized_manager_name] = id_usuario
                print(f"Created user with ID: {id_usuario}")

            if id_usuario:
                nivel_admin = 3 if manager['Nivel'] == 0 else manager['Nivel']
                estado_admin = 1 if any(name.upper() in clean_name_for_db(manager['Responsable']).upper() for name in special_status_names) else 0
                
                admin_records_to_insert.append({
                    'id': manager['Id'],
                    'id_usuario': id_usuario,
                    'nivel_admin': nivel_admin,
                    'cargo': 's/c', # Use 's/c' instead of None
                    'estado_admin': estado_admin
                })

        # 4. Use COPY for bulk insert
        if admin_records_to_insert:
            print(f"Preparing {len(admin_records_to_insert)} admin records for bulk insert...")
            pg_cur.execute("CREATE TEMP TABLE temp_admins (LIKE tbl_admins INCLUDING DEFAULTS);")
            
            csv_buffer = io.StringIO()
            for rec in admin_records_to_insert:
                # Use the value directly, as it's now 's/c'
                cargo = rec['cargo']
                csv_buffer.write(f"{rec['id']}\t{rec['id_usuario']}\t{rec['nivel_admin']}\t{cargo}\t{rec['estado_admin']}\n")
            
            csv_buffer.seek(0)
            copy_sql = "COPY temp_admins (id, id_usuario, nivel_admin, cargo, estado_admin) FROM STDIN"
            pg_cur.copy_expert(sql=copy_sql, file=csv_buffer)
            
            merge_sql = """
                INSERT INTO tbl_admins (id, id_usuario, nivel_admin, cargo, estado_admin)
                SELECT id, id_usuario, nivel_admin, cargo, estado_admin FROM temp_admins
                ON CONFLICT (id) DO UPDATE SET
                    id_usuario = EXCLUDED.id_usuario,
                    nivel_admin = EXCLUDED.nivel_admin,
                    cargo = EXCLUDED.cargo,
                    estado_admin = EXCLUDED.estado_admin;
            """
            pg_cur.execute(merge_sql)
            print(f"Merged {pg_cur.rowcount} records into tbl_admins.")

        pg_conn.commit()
        print("Successfully migrated tbl_admins data with improved matching.")

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
    migrar_tbl_admins()
