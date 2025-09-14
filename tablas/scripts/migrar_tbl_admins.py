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
    if not isinstance(name, str): return ''
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    name = name.lower().replace(',', '')
    name = re.sub(r'^(dr\.|dra\.|mg\.|msc\.|ing\.|lic\.|enf\.)\s*', '', name)
    return ' '.join(name.split())

def clean_name_for_db(name):
    if not isinstance(name, str): return ''
    name = re.sub(r'^(Dr\.|Dra\.|Mg\.|Msc\.|Ing\.|Lic\.|Enf\.)\s*', '', name, flags=re.IGNORECASE)
    return ' '.join(name.split())

def is_valid_dni(doc_id):
    return doc_id and doc_id.isdigit() and len(doc_id) == 8

def migrar_tbl_admins():
    mysql_conn = None
    pg_conn = None
    try:
        mysql_conn = get_mysql_pilar3_connection()
        pg_conn = get_postgres_connection()
        pg_cur = pg_conn.cursor()

        print("--- Iniciando migración final de tbl_admins ---")

        # 1. PREPARAR MAPEO MANUAL
        print("INFO: Configurando mapeo manual de IDs...")
        
        pg_cur.execute("SELECT MAX(id_usuario) FROM tbl_coordinadores")
        last_coord_user = pg_cur.fetchone()
        id_ultimo_coordinador = last_coord_user[0] if last_coord_user and last_coord_user[0] is not None else None
        if not id_ultimo_coordinador:
            print("WARN: No se encontró el último usuario de coordinadores. La regla para el Admin 15 no se aplicará.")

        MAPEO_MANUAL_IDS = {
            1: 27271,  # ID de sistema proporcionado por el usuario
            9: 4566,
            10: 20272,
            11: 20272,
            12: 23260,
            13: 23438,
            17: 23462
        }
        if id_ultimo_coordinador:
            MAPEO_MANUAL_IDS[15] = id_ultimo_coordinador
        
        print("INFO: Mapeo manual final configurado:", MAPEO_MANUAL_IDS)

        # 2. Cargar usuarios existentes en memoria para búsquedas rápidas
        pg_cur.execute("SELECT id, num_doc_identidad, CONCAT_WS(' ', nombres, apellidos) as full_name FROM tbl_usuarios")
        users_by_dni = {row[1]: row[0] for row in pg_cur.fetchall() if row[1]}
        pg_cur.execute("SELECT id, num_doc_identidad, CONCAT_WS(' ', nombres, apellidos) as full_name FROM tbl_usuarios")
        users_by_name = {normalize_name(row[2]): row[0] for row in pg_cur.fetchall() if row[2]}

        # 3. Obtener todos los managers de MySQL
        mysql_cur = mysql_conn.cursor(dictionary=True)
        mysql_cur.execute("SELECT Id, Usuario, Responsable, Nivel FROM tblManagers")
        managers = mysql_cur.fetchall()

        admin_records_to_insert = []
        special_status_ids = {4, 7, 15, 18, 20} # REGLA FINAL PARA ESTADO

        # 4. Procesar cada manager con la lógica final
        for manager in managers:
            mysql_id = manager['Id']
            responsable = manager['Responsable']
            usuario_mysql = manager['Usuario']
            id_usuario = None

            # La salida se ha omitido para una ejecución más limpia
            # print(f"--- Procesando Admin ID: {mysql_id}, Nombre: '{responsable}' ---")

            if mysql_id in MAPEO_MANUAL_IDS:
                id_usuario = MAPEO_MANUAL_IDS[mysql_id]
            else:
                normalized_manager_name = normalize_name(responsable)
                doc_id_to_check = usuario_mysql if is_valid_dni(usuario_mysql) else None

                if doc_id_to_check and doc_id_to_check in users_by_dni:
                    id_usuario = users_by_dni[doc_id_to_check]
                elif normalized_manager_name in users_by_name:
                    id_usuario = users_by_name[normalized_manager_name]
                else:
                    doc_id_to_use = doc_id_to_check if doc_id_to_check else f"ADMIN_{mysql_id}"
                    
                    name_parts = clean_name_for_db(responsable).split()
                    nombres = name_parts[0] if len(name_parts) > 0 else ''
                    apellidos = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                    placeholder_email = f"user.{doc_id_to_use}@migracion.vriunap.edu.pe"

                    pg_cur.execute(
                        "INSERT INTO tbl_usuarios (num_doc_identidad, nombres, apellidos, correo) VALUES (%s, %s, %s, %s) ON CONFLICT (num_doc_identidad) DO NOTHING RETURNING id;",
                        (doc_id_to_use, nombres, apellidos, placeholder_email)
                    )
                    new_user = pg_cur.fetchone()
                    if new_user:
                        id_usuario = new_user[0]
                        users_by_dni[doc_id_to_use] = id_usuario
                        users_by_name[normalized_manager_name] = id_usuario
                    else:
                        pg_cur.execute("SELECT id FROM tbl_usuarios WHERE num_doc_identidad = %s", (doc_id_to_use,))
                        id_usuario = pg_cur.fetchone()[0]

            if id_usuario:
                nivel_admin = 3 if manager['Nivel'] == 0 else manager['Nivel']
                estado_admin = 1 if mysql_id in special_status_ids else 0 # LÓGICA DE ESTADO FINAL
                
                admin_records_to_insert.append({
                    'id': manager['Id'], 'id_usuario': id_usuario, 'nivel_admin': nivel_admin,
                    'cargo': 's/c', 'estado_admin': estado_admin
                })

        # 5. Inserción masiva final
        if admin_records_to_insert:
            print(f"\nINFO: Preparando {len(admin_records_to_insert)} registros para inserción masiva...")
            csv_buffer = io.StringIO()
            for rec in admin_records_to_insert:
                csv_buffer.write(f"{rec['id']}\t{rec['id_usuario']}\t{rec['nivel_admin']}\t{rec['cargo']}\t{rec['estado_admin']}\n")
            csv_buffer.seek(0)
            
            pg_cur.execute("CREATE TEMP TABLE temp_admins (LIKE tbl_admins INCLUDING DEFAULTS);")
            pg_cur.copy_expert("COPY temp_admins (id, id_usuario, nivel_admin, cargo, estado_admin) FROM STDIN", csv_buffer)
            pg_cur.execute("""
                INSERT INTO tbl_admins (id, id_usuario, nivel_admin, cargo, estado_admin)
                SELECT id, id_usuario, nivel_admin, cargo, estado_admin FROM temp_admins
                ON CONFLICT (id) DO UPDATE SET
                    id_usuario = EXCLUDED.id_usuario, nivel_admin = EXCLUDED.nivel_admin,
                    cargo = EXCLUDED.cargo, estado_admin = EXCLUDED.estado_admin;
            """)
            print(f"INFO: Se han insertado o actualizado {pg_cur.rowcount} registros en tbl_admins.")

        pg_conn.commit()
        print("\n--- Migración de tbl_admins finalizada exitosamente. ---")

    except Exception as e:
        print(f"ERROR: Ocurrió un error crítico: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if mysql_conn: mysql_conn.close()
        if pg_conn: pg_conn.close()

if __name__ == "__main__":
    migrar_tbl_admins()
