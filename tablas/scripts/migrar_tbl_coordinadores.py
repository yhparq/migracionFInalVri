import sys
import os
import pandas as pd
import re
import io
import unicodedata
import random

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def normalize_name(name):
    """
    Normalizes a name for robust matching by removing accents, prefixes,
    converting to uppercase, and standardizing whitespace.
    """
    if not isinstance(name, str):
        return ''
    
    # Strip leading/trailing whitespace FIRST
    name = name.strip()
    
    # Remove accents
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    
    # Uppercase
    name = name.upper()
    
    # Remove common prefixes (Dr., Mg., etc.) with optional dots.
    # This is done BEFORE removing all dots to handle cases like 'D.Sc.'
    prefix_pattern = r'^((DR|DRA|MG|MSC|ING|LIC|ENF|SC|D\.SC)\.?\s*)+' # Corrected escaping for dot
    name = re.sub(prefix_pattern, '', name)
    
    # Remove remaining commas and dots
    name = name.replace(',', '').replace('.', '')
    
    # Standardize internal whitespace to a single space
    return ' '.join(name.split())

def clean_name_for_db(name):
    """
    A simpler cleaner for inserting names into the DB, preserving case.
    """
    if not isinstance(name, str):
        return ''
    name = re.sub(r'^(Dr\.|Dra\.|Mg\.|Msc\.|Ing\.|Lic\.|Enf\.|Sc\.)\s*', '', name, flags=re.IGNORECASE)
    return ' '.join(name.split())

def sanitize_for_copy(value):
    """
    Sanitizes a value for the COPY command by removing newlines and tabs.
    """
    if value is None:
        return r'\N' # Represents NULL for PostgreSQL COPY
    
    clean_value = str(value).replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    return ' '.join(clean_value.split())

def migrar_tbl_coordinadores():
    """
    Migrates secretaries from tblSecres using fuzzy string matching with pg_trgm.
    """
    mysql_conn = None
    pg_conn = None
    
    # Mapeo manual para IDs de coordinadores (MySQL) a IDs de usuarios (PostgreSQL)
    # que el algoritmo no puede resolver correctamente.
    MAPEO_MANUAL_IDS = {
        25: 99,  # Forzar que el Coordinador 25 (Pedro Coila- MEDICINA...) sea el Usuario 99
        # Agrega aquí otros mapeos conocidos, por ejemplo:
        # 29: ID_DEL_USUARIO_CORRECTO,
    }

    try:
        mysql_conn = get_mysql_pilar3_connection()
        pg_conn = get_postgres_connection()
        pg_cur = pg_conn.cursor()

        # Fetch secretaries from MySQL
        mysql_cur = mysql_conn.cursor(dictionary=True)
        mysql_cur.execute("SELECT Id, UserLevel, Estado, Resp, Usuario, Celular, Correo, Direccion, Horario FROM tblSecres")
        secretaries = mysql_cur.fetchall()

        coordinador_records_to_insert = []
        
        print("--- Iniciando migración de coordinadores ---")

        # Process each secretary one by one
        for sec in secretaries:
            coordinador_id_mysql = sec['Id']
            original_sec_name = sec['Resp']
            mysql_user = sec['Usuario']
            id_usuario = None

            print(f"\n--- Processing Coordinator ID: {coordinador_id_mysql}, Name: '{original_sec_name}' ---")

            # Prioridad 1: Mapeo Manual
            if coordinador_id_mysql in MAPEO_MANUAL_IDS:
                id_usuario = MAPEO_MANUAL_IDS[coordinador_id_mysql]
                print(f"DEBUG: Manual mapping found. Using User ID: {id_usuario}")
            
            # Prioridad 2: Placeholder names ('----', '-')
            elif original_sec_name in ('----', '-'):
                print("DEBUG: Placeholder name detected.")
                if not mysql_user:
                    print(f"DEBUG: Skipping coordinator ID {coordinador_id_mysql}, placeholder name and no mysql_user.")
                    continue
                
                print(f"DEBUG: Searching for user with num_doc '{mysql_user}'.")
                pg_cur.execute("SELECT id FROM tbl_usuarios WHERE num_doc_identidad = %s", (mysql_user,))
                user_match = pg_cur.fetchone()

                if user_match:
                    id_usuario = user_match[0]
                    print(f"DEBUG: Found existing user for placeholder. User ID: {id_usuario}")
                else:
                    print("DEBUG: Placeholder user not found. Creating new user.")
                    random_doc_id = str(random.randint(10000000, 99999999))
                    new_user_name = f"Usuario Coordinador {mysql_user}"
                    placeholder_email = f"coord.{mysql_user.lower()}.{random_doc_id}@migracion.vriunap.edu.pe"
                    
                    pg_cur.execute(
                        "INSERT INTO tbl_usuarios (num_doc_identidad, nombres, apellidos, correo) VALUES (%s, %s, %s, %s) RETURNING id;",
                        (random_doc_id, new_user_name, '', placeholder_email)
                    )
                    print("DEBUG: Executed INSERT for placeholder user.")
                    insert_result = pg_cur.fetchone()
                    if insert_result:
                        id_usuario = insert_result[0]
                        print(f"DEBUG: Successfully created placeholder user. New User ID: {id_usuario}")
                    else:
                        print(f"CRITICAL: Failed to create placeholder user for {mysql_user}. Skipping coordinator.")
                        continue

            # Prioridad 3: Lógica de Matching Inteligente
            else:
                print("DEBUG: Entering intelligent matching logic.")
                cleaned_name = re.split(r'[-_]', original_sec_name)[0].strip()
                normalized_sec_name = normalize_name(cleaned_name)
                print(f"DEBUG: Original Name: '{original_sec_name}' -> Cleaned: '{cleaned_name}' -> Normalized: '{normalized_sec_name}'")

                if not normalized_sec_name or len(normalized_sec_name) < 4:
                    print(f"DEBUG: Skipping invalid coordinator name.")
                    continue

                find_user_query = """
                    SELECT id, full_name, similarity_score FROM (
                        SELECT id, REGEXP_REPLACE(CONCAT_WS(' ', TRIM(nombres), TRIM(apellidos)), '\s+', ' ', 'g') as full_name,
                        similarity(%s, UPPER(REGEXP_REPLACE(CONCAT_WS(' ', TRIM(nombres), TRIM(apellidos)), '\s+', ' ', 'g'))) as similarity_score
                        FROM tbl_usuarios
                    ) AS candidates
                    WHERE similarity_score >= 0.7 ORDER BY similarity_score DESC LIMIT 1;
                """
                print(f"DEBUG: Executing similarity search for '{normalized_sec_name}'.")
                pg_cur.execute(find_user_query, (normalized_sec_name,))
                best_match = pg_cur.fetchone()

                if best_match:
                    user_id, matched_name, score = best_match
                    id_usuario = user_id
                    print(f"DEBUG: Match found for '{original_sec_name}' -> '{matched_name}' with score {score:.2f}. Using user ID: {id_usuario}")
                else:
                    doc_id_to_use = f"COORD_{coordinador_id_mysql}"
                    print(f"DEBUG: No match found. Attempting to create new user with doc_id '{doc_id_to_use}'.")
                    new_user_name = f"coordinador {clean_name_for_db(original_sec_name)}"
                    placeholder_email = f"coord.{coordinador_id_mysql}@migracion.vriunap.edu.pe"

                    pg_cur.execute(
                        "INSERT INTO tbl_usuarios (num_doc_identidad, nombres, apellidos, correo) VALUES (%s, %s, %s, %s) ON CONFLICT (num_doc_identidad) DO NOTHING RETURNING id;",
                        (doc_id_to_use, new_user_name, '', placeholder_email)
                    )
                    print("DEBUG: Executed INSERT ON CONFLICT for new user.")
                    result = pg_cur.fetchone()
                    if result:
                        id_usuario = result[0]
                        print(f"DEBUG: Successfully created new user. New User ID: {id_usuario}")
                    else:
                        print(f"DEBUG: INSERT failed (likely conflict). Searching for existing user with doc_id '{doc_id_to_use}'.")
                        pg_cur.execute("SELECT id FROM tbl_usuarios WHERE num_doc_identidad = %s", (doc_id_to_use,))
                        select_result = pg_cur.fetchone()
                        if select_result:
                            id_usuario = select_result[0]
                            print(f"DEBUG: Found existing user after conflict. User ID: {id_usuario}")
                        else:
                            print(f"CRITICAL: Failed to create or find user for COORD_{coordinador_id_mysql}. Skipping coordinator.")
                            continue
            
            if id_usuario:
                print(f"DEBUG: Preparing to add Coordinator ID {coordinador_id_mysql} with User ID {id_usuario} to insert list.")
                coordinador_records_to_insert.append({
                    'id': coordinador_id_mysql, 'id_usuario': id_usuario, 'nivel_coordinador': sec['UserLevel'],
                    'correo_oficina': sec['Correo'], 'direccion_oficina': sec['Direccion'], 'horario': sec['Horario'],
                    'telefono': sec['Celular'], 'estado_coordinador': sec['Estado']
                })
            else:
                print(f"WARNING: No id_usuario was assigned for Coordinator ID {coordinador_id_mysql}. This record will be skipped.")

        # Use COPY for bulk insert
        if coordinador_records_to_insert:
            print(f"\nDEBUG: Preparing {len(coordinador_records_to_insert)} coordinator records for bulk insert...")
            pg_cur.execute("CREATE TEMP TABLE temp_coordinadores (LIKE tbl_coordinadores INCLUDING DEFAULTS);")
            
            csv_buffer = io.StringIO()
            for rec in coordinador_records_to_insert:
                sanitized_values = [
                    sanitize_for_copy(rec['id']), sanitize_for_copy(rec['id_usuario']), sanitize_for_copy(rec['nivel_coordinador']),
                    sanitize_for_copy(rec['correo_oficina']), sanitize_for_copy(rec['direccion_oficina']), sanitize_for_copy(rec['horario']),
                    sanitize_for_copy(rec['telefono']), sanitize_for_copy(rec['estado_coordinador'])
                ]
                csv_buffer.write('\t'.join(sanitized_values) + '\n')
            
            csv_buffer.seek(0)
            copy_sql = "COPY temp_coordinadores (id, id_usuario, nivel_coordinador, correo_oficina, direccion_oficina, horario, telefono, estado_coordinador) FROM STDIN"
            pg_cur.copy_expert(sql=copy_sql, file=csv_buffer)
            print("DEBUG: COPY to temp table complete.")
            
            merge_sql = """
                INSERT INTO tbl_coordinadores (id, id_usuario, nivel_coordinador, correo_oficina, direccion_oficina, horario, telefono, estado_coordinador)
                SELECT id, id_usuario, nivel_coordinador, correo_oficina, direccion_oficina, horario, telefono, estado_coordinador FROM temp_coordinadores
                ON CONFLICT (id) DO UPDATE SET
                    id_usuario = EXCLUDED.id_usuario, nivel_coordinador = EXCLUDED.nivel_coordinador,
                    correo_oficina = EXCLUDED.correo_oficina, direccion_oficina = EXCLUDED.direccion_oficina,
                    horario = EXCLUDED.horario, telefono = EXCLUDED.telefono, estado_coordinador = EXCLUDED.estado_coordinador;
            """
            pg_cur.execute(merge_sql)
            print(f"DEBUG: Merged {pg_cur.rowcount} records into tbl_coordinadores.")

        pg_conn.commit()
        print("\nSuccessfully migrated tbl_coordinadores data with fuzzy matching.")

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
    migrar_tbl_coordinadores()
