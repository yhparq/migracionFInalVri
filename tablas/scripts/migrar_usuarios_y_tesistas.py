import sys
import os
import io
import csv
import psycopg2
import mysql.connector

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def migrate_usuarios_y_tesistas_fast_v2():
    """
    Migra tesistas a usuarios y tesistas. Asegura que cada persona sea única en
    tbl_usuarios, pero migra todos los registros originales a tbl_tesistas.
    """
    print("--- Iniciando migración (v2) de Usuarios y Tesistas ---")
    mysql_conn = None
    postgres_conn = None
    
    try:
        # 1. Establecer conexiones
        mysql_conn = get_mysql_pilar3_connection()
        postgres_conn = get_postgres_connection()

        if not all([mysql_conn, postgres_conn]):
            raise Exception("No se pudieron establecer las conexiones a la base de datos.")

        mysql_cursor = mysql_conn.cursor(dictionary=True)
        postgres_cursor = postgres_conn.cursor()

        # 2. Pre-cargar datos de usuarios existentes
        print("Leyendo usuarios existentes desde PostgreSQL...")
        postgres_cursor.execute("SELECT lower(trim(nombres) || ' ' || trim(apellidos)), id, correo, num_doc_identidad FROM tbl_usuarios")
        existing_users_raw = postgres_cursor.fetchall()
        
        # Mapas para una búsqueda eficiente
        existing_user_map_by_name = {row[0]: {'id': row[1], 'correo': row[2], 'dni': row[3]} for row in existing_users_raw}
        existing_emails = {row[2] for row in existing_users_raw if row[2]}
        existing_dnis = {row[3] for row in existing_users_raw if row[3]}
        print(f"Se encontraron {len(existing_user_map_by_name)} usuarios existentes.")

        # 3. Leer todos los tesistas de MySQL
        print("Leyendo registros de tblTesistas desde MySQL...")
        mysql_cursor.execute("SELECT * FROM tblTesistas")
        tesistas_records = mysql_cursor.fetchall()
        print(f"Se encontraron {len(tesistas_records)} registros de tesistas para procesar.")

        # --- ETAPA 1: IDENTIFICAR Y CREAR USUARIOS ÚNICOS ---

        new_users_to_create = {} # Usamos un dict para garantizar unicidad por nombre
        processed_dnis = set(existing_dnis)
        
        for record in tesistas_records:
            nombres = record.get('Nombres', '').strip()
            apellidos = record.get('Apellidos', '').strip()
            if not nombres or not apellidos:
                continue

            full_name_key = f"{nombres.lower()} {apellidos.lower()}"

            # Si la persona ya existe (como docente o como tesista ya procesado), no la creamos de nuevo
            if full_name_key in existing_user_map_by_name or full_name_key in new_users_to_create:
                continue

            # Manejo de DNI y Correo para el nuevo usuario
            dni = (record.get('DNI') or '').strip()
            if not dni or dni in processed_dnis:
                dni = f"sd_{full_name_key.replace(' ','_')}"[:12] # DNI generado si está vacío o duplicado
            processed_dnis.add(dni)

            email = (record.get('Correo') or '').strip()
            if not email or email in existing_emails:
                email = f"dni.{dni}@unap.edu.pe"
            existing_emails.add(email)

            new_users_to_create[full_name_key] = (
                nombres, apellidos, 'DNI', dni, email, None, record.get('NroCelular'),
                None, record.get('Direccion'), record.get('Sexo'), None,
                record.get('Clave'), None, 1
            )

        if new_users_to_create:
            print(f"Etapa 1: Se crearán {len(new_users_to_create)} nuevos usuarios únicos.")
            usuarios_to_insert = list(new_users_to_create.values())
            
            buffer_usuarios = io.StringIO()
            writer_usuarios = csv.writer(buffer_usuarios, delimiter='\t', quotechar='"')
            writer_usuarios.writerows(usuarios_to_insert)
            buffer_usuarios.seek(0)

            cols_usuarios = ('nombres', 'apellidos', 'tipo_doc_identidad', 'num_doc_identidad', 'correo', 'correo_google', 'telefono', 'pais', 'direccion', 'sexo', 'fecha_nacimiento', 'contrasenia', 'ruta_foto', 'estado')
            postgres_cursor.copy_expert(f"COPY public.tbl_usuarios ({', '.join(cols_usuarios)}) FROM STDIN WITH CSV DELIMITER AS E'\t'", buffer_usuarios)
        
        # --- ETAPA 2: MIGRAR TODOS LOS REGISTROS A TBL_TESISTAS ---

        print("Actualizando mapa de usuarios con las nuevas inserciones...")
        postgres_cursor.execute("SELECT lower(trim(nombres) || ' ' || trim(apellidos)), id FROM tbl_usuarios")
        final_user_map_by_name = {row[0]: row[1] for row in postgres_cursor.fetchall()}
        print(f"Mapa final de usuarios contiene {len(final_user_map_by_name)} entradas.")

        tesistas_to_insert_final = []
        for record in tesistas_records:
            nombres = record.get('Nombres', '').strip()
            apellidos = record.get('Apellidos', '').strip()
            if not nombres or not apellidos:
                continue
            
            full_name_key = f"{nombres.lower()} {apellidos.lower()}"
            new_user_id = final_user_map_by_name.get(full_name_key)

            if new_user_id:
                codigo_estudiante = (record.get('Codigo') or '').strip()
                if not codigo_estudiante:
                    codigo_estudiante = 'S/COD'
                else:
                    codigo_estudiante = codigo_estudiante[:6]

                tesistas_to_insert_final.append(
                    (new_user_id, codigo_estudiante, record.get('IdCarrera'), 
                     1, record.get('Id'))
                )

        if tesistas_to_insert_final:
            print(f"Etapa 2: Se insertarán {len(tesistas_to_insert_final)} registros en tbl_tesistas.")
            buffer_tesistas = io.StringIO()
            writer_tesistas = csv.writer(buffer_tesistas, delimiter='\t', quotechar='"')
            writer_tesistas.writerows(tesistas_to_insert_final)
            buffer_tesistas.seek(0)

            cols_tesistas = ('id_usuario', 'codigo_estudiante', 'id_estructura_academica', 'estado', 'id_antiguo')
            postgres_cursor.copy_expert(f"COPY public.tbl_tesistas ({', '.join(cols_tesistas)}) FROM STDIN WITH CSV DELIMITER AS E'\t'", buffer_tesistas)

        postgres_conn.commit()
        print("Migración combinada de tesistas (v2) completada exitosamente.")

    except (Exception, psycopg2.Error, mysql.connector.Error) as e:
        print(f"Error durante la migración de tesistas (v2): {e}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if mysql_conn: mysql_conn.close()
        if postgres_conn: postgres_conn.close()
        print("--- Migración combinada de Usuarios y Tesistas (v2) finalizada ---")

if __name__ == '__main__':
    migrate_usuarios_y_tesistas_fast_v2()
