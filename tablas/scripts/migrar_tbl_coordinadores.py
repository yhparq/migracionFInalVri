import sys
import os
import re
import io
import unicodedata
import random

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def normalize_name(name):
    if not isinstance(name, str): return ''
    name = name.strip()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    name = name.upper()
    prefix_pattern = r'^((DR|DRA|MG|MSC|ING|LIC|ENF|SC|D\.SC)\.?\s*)+'
    name = re.sub(prefix_pattern, '', name)
    name = name.replace(',', '').replace('.', '')
    return ' '.join(name.split())

def clean_name_for_db(name):
    if not isinstance(name, str): return ''
    name = re.sub(r'^(Dr\.|Dra\.|Mg\.|Msc\.|Ing\.|Lic\.|Enf\.|Sc\.)\s*', '', name, flags=re.IGNORECASE)
    return ' '.join(name.split())

def parse_full_name(name_str):
    parts = name_str.strip().split()
    if len(parts) <= 1: return name_str, ''
    elif len(parts) == 2: return parts[0], parts[1]
    elif len(parts) == 3: return parts[0], f"{parts[1]} {parts[2]}"
    elif len(parts) >= 4: return f"{parts[0]} {parts[1]}", f"{parts[2]} {parts[3]}"
    return name_str, ''

def sanitize_for_copy(value):
    if value is None: return r'\N'
    clean_value = str(value).replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    return ' '.join(clean_value.split())

def migrar_tbl_coordinadores():
    mysql_conn = None
    pg_conn = None
    
    MAPEO_MANUAL_IDS = { 25: 99, 59: 17706, 98: 207 }
    MAPEO_POR_NOMBRE = { 235: "Katherine J. Cutimbo Samaniego" }
    CREATE_FROM_USERNAME_IDS = [
        6, 15, 57, 58, 59, 60, 62, 63, 65, 67, 73, 74, 96, 97, 102, 
        135, 139, 141, 180, 181, 197, 193, 233
    ]

    try:
        mysql_conn = get_mysql_pilar3_connection()
        pg_conn = get_postgres_connection()
        pg_cur = pg_conn.cursor()

        mysql_cur = mysql_conn.cursor(dictionary=True)
        mysql_cur.execute("SELECT Id, Id_Facultad, UserLevel, Estado, Resp, Usuario, Celular, Correo, Direccion, Horario FROM tblSecres")
        secretaries = mysql_cur.fetchall()

        coordinador_records_to_insert = []
        print("--- Iniciando migración final de coordinadores con reglas de depuración ---")

        for sec in secretaries:
            coordinador_id_mysql = sec['Id']
            original_sec_name = sec['Resp']
            mysql_user = sec['Usuario']
            id_usuario = None

            print(f"\n--- Procesando Coordinador ID: {coordinador_id_mysql}, Nombre: '{original_sec_name}' ---")

            if coordinador_id_mysql in MAPEO_MANUAL_IDS:
                id_usuario = MAPEO_MANUAL_IDS[coordinador_id_mysql]
                print(f"INFO: Regla de Mapeo Manual por ID. Usando Usuario ID: {id_usuario}")
            elif coordinador_id_mysql in MAPEO_POR_NOMBRE:
                exact_name = MAPEO_POR_NOMBRE[coordinador_id_mysql]
                print(f"INFO: Regla de Mapeo por Nombre. Buscando a '{exact_name}'...")
                pg_cur.execute("SELECT id FROM tbl_usuarios WHERE TRIM(CONCAT_WS(' ', nombres, apellidos)) = %s", (exact_name,))
                user_match = pg_cur.fetchone()
                if user_match:
                    id_usuario = user_match[0]
                    print(f"INFO: Encontrado. Usando Usuario ID: {id_usuario}")
                else:
                    print(f"WARN: No se encontró al usuario '{exact_name}'. Se creará un nuevo usuario.")
                    doc_id_to_use = f"COORD_{coordinador_id_mysql}"
                    nombres, apellidos = parse_full_name(exact_name)
                    placeholder_email = f"coord.{coordinador_id_mysql}@migracion.vriunap.edu.pe"
                    pg_cur.execute(
                        "INSERT INTO tbl_usuarios (num_doc_identidad, nombres, apellidos, correo) VALUES (%s, %s, %s, %s) RETURNING id;",
                        (doc_id_to_use, nombres, apellidos, placeholder_email)
                    )
                    id_usuario = pg_cur.fetchone()[0]
                    print(f"INFO: Nuevo usuario creado. Usuario ID: {id_usuario}")
            elif coordinador_id_mysql in CREATE_FROM_USERNAME_IDS:
                print(f"INFO: Regla de Creación por Usuario. Usando DNI/Usuario: '{mysql_user}'")
                if not mysql_user:
                    print(f"WARN: DNI/Usuario vacío para ID {coordinador_id_mysql}. Saltando.")
                    continue
                doc_id_to_use = mysql_user if len(mysql_user) <= 12 else f"s/d-{coordinador_id_mysql}"
                pg_cur.execute("SELECT id FROM tbl_usuarios WHERE num_doc_identidad = %s", (doc_id_to_use,))
                user_match = pg_cur.fetchone()
                if user_match:
                    id_usuario = user_match[0]
                    print(f"INFO: Usuario existente encontrado por DNI. Usando Usuario ID: {id_usuario}")
                else:
                    print(f"INFO: Creando nuevo usuario para '{doc_id_to_use}'...")
                    if coordinador_id_mysql in [6, 15]:
                        nombres, apellidos = f"Usuario Coordinador {mysql_user}", ''
                    else:
                        nombres, apellidos = parse_full_name(clean_name_for_db(original_sec_name))
                    placeholder_email = f"coord.{mysql_user.lower().replace(' ', '')}@migracion.vriunap.edu.pe"
                    pg_cur.execute(
                        "INSERT INTO tbl_usuarios (num_doc_identidad, nombres, apellidos, correo) VALUES (%s, %s, %s, %s) RETURNING id;",
                        (doc_id_to_use, nombres, apellidos, placeholder_email)
                    )
                    id_usuario = pg_cur.fetchone()[0]
                    print(f"INFO: Nuevo usuario creado. Usuario ID: {id_usuario}")

            if id_usuario is None:
                print("INFO: Sin reglas manuales. Buscando por similitud.")
                if not original_sec_name or original_sec_name.strip() in ('----', '-'):
                    print("WARN: Nombre inválido. Saltando.")
                    continue
                cleaned_name = re.split(r'[-_]', original_sec_name)[0].strip()
                normalized_sec_name = normalize_name(cleaned_name)
                if len(normalized_sec_name) < 4:
                    print("WARN: Nombre demasiado corto. Saltando.")
                    continue
                pg_cur.execute("""
                    SELECT id, full_name, similarity_score FROM (
                        SELECT id, TRIM(CONCAT_WS(' ', nombres, apellidos)) as full_name,
                        similarity(%s, UPPER(TRIM(CONCAT_WS(' ', nombres, apellidos)))) as similarity_score
                        FROM tbl_usuarios
                    ) AS candidates
                    WHERE similarity_score >= 0.7 ORDER BY similarity_score DESC LIMIT 1;
                """, (normalized_sec_name,))
                best_match = pg_cur.fetchone()
                if best_match:
                    id_usuario, matched_name, score = best_match
                    print(f"INFO: Coincidencia: '{original_sec_name}' -> '{matched_name}' ({score:.2f}). ID: {id_usuario}")
                else:
                    print(f"INFO: Sin coincidencia. Creando nuevo usuario para '{original_sec_name}'.")
                    doc_id_to_use = f"COORD_{coordinador_id_mysql}"
                    nombres, apellidos = parse_full_name(clean_name_for_db(original_sec_name))
                    placeholder_email = f"coord.{coordinador_id_mysql}@migracion.vriunap.edu.pe"
                    pg_cur.execute("SELECT id FROM tbl_usuarios WHERE num_doc_identidad = %s", (doc_id_to_use,))
                    existing_user = pg_cur.fetchone()
                    if existing_user:
                        id_usuario = existing_user[0]
                        print(f"INFO: Usuario ya existía con DNI temporal. ID: {id_usuario}")
                    else:
                        pg_cur.execute(
                            "INSERT INTO tbl_usuarios (num_doc_identidad, nombres, apellidos, correo) VALUES (%s, %s, %s, %s) RETURNING id;",
                            (doc_id_to_use, nombres or f"Coordinador {original_sec_name}", apellidos, placeholder_email)
                        )
                        id_usuario = pg_cur.fetchone()[0]
                        print(f"INFO: Nuevo usuario creado con DNI temporal. ID: {id_usuario}")

            if id_usuario:
                id_facultad = sec.get('IdFacultad') or 1 # Usar IdFacultad directamente, con default 1

                coordinador_records_to_insert.append({
                    'id': coordinador_id_mysql, 'id_usuario': id_usuario, 'id_facultad': id_facultad,
                    'nivel_coordinador': sec['UserLevel'], 'correo_oficina': sec['Correo'], 
                    'direccion_oficina': sec['Direccion'], 'horario': sec['Horario'],
                    'telefono': sec['Celular'], 'estado_coordinador': sec['Estado']
                })
            else:
                print(f"ERROR: No se pudo asignar un Usuario ID para el Coordinador ID {coordinador_id_mysql}.")

        if coordinador_records_to_insert:
            print(f"\nINFO: Preparando {len(coordinador_records_to_insert)} registros para inserción masiva...")
            
            csv_buffer = io.StringIO()
            for rec in coordinador_records_to_insert:
                csv_buffer.write('\t'.join([
                    sanitize_for_copy(rec['id']), sanitize_for_copy(rec['id_usuario']), sanitize_for_copy(rec['id_facultad']),
                    sanitize_for_copy(rec['nivel_coordinador']), sanitize_for_copy(rec['correo_oficina']), 
                    sanitize_for_copy(rec['direccion_oficina']), sanitize_for_copy(rec['horario']),
                    sanitize_for_copy(rec['telefono']), sanitize_for_copy(rec['estado_coordinador'])
                ]) + '\n')
            csv_buffer.seek(0)

            with pg_conn.cursor() as cur:
                cur.execute("CREATE TEMP TABLE temp_coordinadores (LIKE tbl_coordinadores INCLUDING DEFAULTS);")
                cur.copy_expert("COPY temp_coordinadores (id, id_usuario, id_facultad, nivel_coordinador, correo_oficina, direccion_oficina, horario, telefono, estado_coordinador) FROM STDIN", csv_buffer)
                cur.execute("""
                    INSERT INTO tbl_coordinadores (id, id_usuario, id_facultad, nivel_coordinador, correo_oficina, direccion_oficina, horario, telefono, estado_coordinador)
                    SELECT id, id_usuario, id_facultad, nivel_coordinador, correo_oficina, direccion_oficina, horario, telefono, estado_coordinador FROM temp_coordinadores
                    ON CONFLICT (id) DO UPDATE SET
                        id_usuario = EXCLUDED.id_usuario, id_facultad = EXCLUDED.id_facultad,
                        nivel_coordinador = EXCLUDED.nivel_coordinador, correo_oficina = EXCLUDED.correo_oficina,
                        direccion_oficina = EXCLUDED.direccion_oficina, horario = EXCLUDED.horario,
                        telefono = EXCLUDED.telefono, estado_coordinador = EXCLUDED.estado_coordinador;
                """
)
                print(f"INFO: Se han insertado o actualizado {cur.rowcount} registros en tbl_coordinadores.")

        pg_conn.commit()
        print("\n--- Migración de tbl_coordinadores finalizada exitosamente. ---")

    except Exception as e:
        print(f"ERROR: Ocurrió un error crítico: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if mysql_conn: mysql_conn.close()
        if pg_conn: pg_conn.close()

if __name__ == "__main__":
    migrar_tbl_coordinadores()
