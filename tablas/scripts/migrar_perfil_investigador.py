import os
import sys
import csv
import psycopg2
import re
import unicodedata

# Add parent directory to Python path to allow module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection

def normalize_name(name):
    """
    Normalizes a name by removing titles, accents, and extra spaces for similarity matching.
    """
    if not isinstance(name, str): return ''
    name = name.strip()
    # Remove accents
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    name = name.upper()
    # Remove titles like Dr., Mg., etc.
    prefix_pattern = r'^((DR|DRA|MG|MSC|ING|LIC|ENF|SC|D\.SC)\.?\s*)+' # Corrected escaping for '.' in regex
    name = re.sub(prefix_pattern, '', name)
    name = name.replace(',', '').replace('.', '')
    return ' '.join(name.split())

def migrate_perfil_investigador_from_csv():
    """
    Populates tbl_perfil_investigador from a CSV file.
    - If IdPilar is 0, creates a new user in tbl_usuarios.
    - If IdPilar is not 0, finds an existing user by name similarity.
    """
    pg_conn = None
    csv_file_path = os.path.join(os.path.dirname(__file__), '..', 'coasesor.csv')

    print("--- Iniciando migración de Perfil de Investigador desde CSV ---")

    try:
        pg_conn = get_postgres_connection()
        if not pg_conn:
            raise Exception("Database connection failed.")

        pg_cursor = pg_conn.cursor()

        profiles_to_insert = []
        
        with open(csv_file_path, mode='r', encoding='latin-1') as infile:
            reader = csv.DictReader(infile, delimiter=';')
            
            for row in reader:
                id_usuario = None
                id_pilar = row.get('IdPilar', '0').strip()
                nombres = row.get('Nombres', '').strip()
                apellidos = row.get('Apellidos', '').strip()
                full_name = f"{nombres} {apellidos}".strip()
                dni = row.get('NumDoc', '').strip()
                correo = row.get('Correo', '').strip()

                print(f"\n--- Procesando CSV Fila: {full_name} (DNI: {dni}) ---")

                # Regla 1: Si IdPilar es 0, es un usuario nuevo
                if id_pilar == '0':
                    print(f"INFO: IdPilar es 0. Tratando como usuario nuevo/externo.")
                    # Evitar duplicados: buscar por DNI o correo
                    pg_cursor.execute(
                        "SELECT id FROM tbl_usuarios WHERE num_doc_identidad = %s OR correo = %s",
                        (dni, correo)
                    )
                    user_match = pg_cursor.fetchone()

                    if user_match:
                        id_usuario = user_match[0]
                        print(f"INFO: Usuario ya existía con DNI/correo. Usando id_usuario: {id_usuario}")
                    else:
                        # Si no hay DNI, crear uno temporal para cumplir con la restricción NOT NULL
                        doc_para_insertar = dni
                        if not doc_para_insertar:
                            csv_id = row.get('Id', '').strip()
                            doc_para_insertar = f"EXT-COAS-{csv_id}"
                            print(f"WARN: DNI vacío en CSV. Se usará un DNI temporal: '{doc_para_insertar}'")

                        if not doc_para_insertar and not correo:
                            print(f"WARN: Se requiere DNI o Correo para crear un nuevo usuario. Saltando fila.")
                            continue
                        
                        print(f"INFO: Creando nuevo usuario para '{full_name}'...")
                        insert_query = """
                            INSERT INTO tbl_usuarios (nombres, apellidos, num_doc_identidad, correo, estado)
                            VALUES (%s, %s, %s, %s, 1) RETURNING id;
                        """
                        pg_cursor.execute(insert_query, (nombres, apellidos, doc_para_insertar, correo or None))
                        id_usuario = pg_cursor.fetchone()[0]
                        print(f"INFO: Nuevo usuario creado con id_usuario: {id_usuario}")
                
                # Regla 2: Si IdPilar no es 0, buscar por similitud de nombre
                else:
                    print(f"INFO: IdPilar es {id_pilar}. Buscando usuario existente por similitud de nombre.")
                    normalized_full_name = normalize_name(full_name)
                    
                    if len(normalized_full_name) < 4:
                        print(f"WARN: Nombre '{full_name}' demasiado corto para búsqueda fiable. Saltando.")
                        continue

                    pg_cursor.execute(
                        """
                        SELECT id, full_name, similarity_score FROM (
                            SELECT id, TRIM(CONCAT_WS(' ', nombres, apellidos)) as full_name,
                            similarity(%s, UPPER(TRIM(CONCAT_WS(' ', nombres, apellidos)))) as similarity_score
                            FROM tbl_usuarios
                        ) AS candidates
                        WHERE similarity_score >= 0.6 ORDER BY similarity_score DESC LIMIT 1;
                    """, (normalized_full_name,))
                    best_match = pg_cursor.fetchone()

                    if best_match:
                        id_usuario = best_match[0]
                        matched_name = best_match[1]
                        score = best_match[2]
                        print(f"INFO: Coincidencia encontrada: '{full_name}' -> '{matched_name}' (Score: {score:.2f}). Usando id_usuario: {id_usuario}")
                    else:
                        print(f"WARN: No se encontró un usuario coincidente para '{full_name}'. Saltando.")
                        continue

                # Si se obtuvo un id_usuario, preparar el perfil para inserción
                if id_usuario:
                    profiles_to_insert.append((
                        id_usuario,
                        None,  # institucion
                        None,  # afiliacion
                        row.get('ORCID') or None,
                        row.get('ctivitaeID') or None,
                        row.get('Renacyt') or None,
                        row.get('Nivel') or None,
                        row.get('ScopusID') or None,
                        None,  # wos_id
                        None,  # alternativo_scopus_id
                        1      # estado_investigador (por defecto 1)
                    ))

        # Inserción masiva de los perfiles
        if profiles_to_insert:
            print(f"\n--- Insertando/Actualizando {len(profiles_to_insert)} perfiles de investigador ---")
            
            insert_query = """
                INSERT INTO tbl_perfil_investigador (
                    id_usuario, institucion, afiliacion, orcid, ctivitae, 
                    codigo_renacyt, nivel_renacyt, scopus_id, wos_id, 
                    alternativo_scopus_id, estado_investigador
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_usuario) DO UPDATE SET
                    institucion = EXCLUDED.institucion,
                    afiliacion = EXCLUDED.afiliacion,
                    orcid = EXCLUDED.orcid,
                    ctivitae = EXCLUDED.ctivitae,
                    codigo_renacyt = EXCLUDED.codigo_renacyt,
                    nivel_renacyt = EXCLUDED.nivel_renacyt,
                    scopus_id = EXCLUDED.scopus_id,
                    wos_id = EXCLUDED.wos_id,
                    alternativo_scopus_id = EXCLUDED.alternativo_scopus_id,
                    estado_investigador = EXCLUDED.estado_investigador;
            """
            pg_cursor.executemany(insert_query, profiles_to_insert)
            pg_conn.commit()
            print(f"--- Migración de perfiles completada. Se procesaron {pg_cursor.rowcount} registros. ---")
        else:
            print("--- No se encontraron perfiles válidos para migrar. ---")

    except (Exception, psycopg2.Error) as e:
        print(f"ERROR: Ocurrió un error durante la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        print("INFO: Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    migrate_perfil_investigador_from_csv()
