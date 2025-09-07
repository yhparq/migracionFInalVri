import sys
import os
import io
import csv
import psycopg2
import mysql.connector

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_absmain_connection, get_postgres_connection

def migrate_usuarios_y_docentes_fast():
    """
    Migra datos de tblDocentes (MySQL) a tbl_usuarios y tbl_docentes (PostgreSQL)
    en un proceso de dos etapas de alto rendimiento usando COPY.
    """
    print("--- Iniciando migración combinada de Usuarios y Docentes ---")
    mysql_conn = None
    postgres_conn = None
    
    try:
        # 1. Establecer conexiones
        mysql_conn = get_mysql_absmain_connection()
        postgres_conn = get_postgres_connection()

        if not all([mysql_conn, postgres_conn]):
            raise Exception("No se pudieron establecer las conexiones a la base de datos.")

        mysql_cursor = mysql_conn.cursor(dictionary=True)
        postgres_cursor = postgres_conn.cursor()

        # 2. Pre-cargar correos existentes para evitar duplicados
        print("Obteniendo correos existentes de tbl_usuarios en PostgreSQL...")
        postgres_cursor.execute("SELECT correo FROM tbl_usuarios WHERE correo IS NOT NULL")
        existing_emails = {row[0] for row in postgres_cursor.fetchall()}
        print(f"Se encontraron {len(existing_emails)} correos existentes.")

        # 3. Leer todos los docentes de MySQL
        print("Leyendo registros de tblDocentes desde MySQL...")
        mysql_cursor.execute("SELECT * FROM tblDocentes")
        docentes_records = mysql_cursor.fetchall()
        print(f"Se encontraron {len(docentes_records)} registros de docentes.")

        # --- ETAPA 1: MIGRAR A TBL_USUARIOS ---
        
        usuarios_to_insert = []
        valid_docente_records = []
        emails_in_batch = set()
        
        for record in docentes_records:
            email = record.get('Correo')
            dni = record.get('DNI')

            if not email or not email.strip():
                if dni and dni.strip():
                    email = f"dni.{dni.strip()}@unap.edu.pe"
                else:
                    continue
            
            if email in existing_emails or email in emails_in_batch:
                continue
            
            emails_in_batch.add(email)
            record['generated_email'] = email # Guardamos el email que se usará
            valid_docente_records.append(record)

            estado = 1 if str(record.get('Activo')).strip().upper() == 'A' else 0

            usuarios_to_insert.append(( 
                record.get('Nombres'), record.get('Apellidos'), 'DNI', dni, email,
                None, record.get('NroCelular'), None, record.get('Direccion'),
                record.get('Sexo'), record.get('FechaNac'), record.get('Clave'),
                None, estado
            ))

        if usuarios_to_insert:
            print(f"Etapa 1: {len(usuarios_to_insert)} registros de usuarios válidos para insertar.")
            buffer_usuarios = io.StringIO()
            writer_usuarios = csv.writer(buffer_usuarios, delimiter='\t', quotechar='"')
            writer_usuarios.writerows(usuarios_to_insert)
            buffer_usuarios.seek(0)

            cols_usuarios = ('nombres', 'apellidos', 'tipo_doc_identidad', 'num_doc_identidad', 'correo', 'correo_google', 'telefono', 'pais', 'direccion', 'sexo', 'fecha_nacimiento', 'contrasenia', 'ruta_foto', 'estado')
            
            print("Iniciando carga masiva en tbl_usuarios...")
            postgres_cursor.copy_expert(f"COPY public.tbl_usuarios ({', '.join(cols_usuarios)}) FROM STDIN WITH CSV DELIMITER AS E'\t'", buffer_usuarios)
            print("Carga masiva en tbl_usuarios completada.")
        else:
            print("Etapa 1: No hay nuevos usuarios para insertar.")

        # --- ETAPA 2: MIGRAR A TBL_DOCENTES ---

        # 4. Crear mapa de correo -> nuevo id_usuario
        print("Creando mapa de correo a nuevo id_usuario...")
        user_map = {}
        if emails_in_batch:
            placeholders = ','.join(['%s'] * len(emails_in_batch))
            postgres_cursor.execute(f"SELECT id, correo FROM tbl_usuarios WHERE correo IN ({placeholders})", tuple(emails_in_batch))
            user_map = {row[1]: row[0] for row in postgres_cursor.fetchall()}
        print(f"Mapa creado con {len(user_map)} nuevas entradas.")

        # 5. Preparar datos para tbl_docentes
        docentes_to_insert = []
        for record in valid_docente_records:
            new_user_id = user_map.get(record['generated_email'])
            if new_user_id:
                # **AQUÍ ESTÁ LA CORRECCIÓN**
                # Si CodAIRH es nulo o vacío, usar 'S/C' como placeholder
                codigo_airhs = record.get('CodAIRH')
                if not codigo_airhs or not codigo_airhs.strip():
                    codigo_airhs = 'S/C'

                # **AQUÍ ESTÁ LA NUEVA CORRECCIÓN**
                # Si IdEspecialidad es nulo o 0, usar 1 como placeholder
                id_especialidad = record.get('IdEspecialidad')
                if not id_especialidad or id_especialidad == 0:
                    id_especialidad = 1

                docentes_to_insert.append(( 
                    new_user_id,
                    record.get('IdCategoria'),
                    codigo_airhs,
                    id_especialidad,
                    1 if str(record.get('Activo')).strip().upper() == 'A' else 0,
                    record.get('Id') # id_antiguo
                ))

        if docentes_to_insert:
            print(f"Etapa 2: {len(docentes_to_insert)} registros de docentes para insertar.")
            buffer_docentes = io.StringIO()
            writer_docentes = csv.writer(buffer_docentes, delimiter='\t', quotechar='"')
            writer_docentes.writerows(docentes_to_insert)
            buffer_docentes.seek(0)

            cols_docentes = ('id_usuario', 'id_categoria', 'codigo_airhs', 'id_especialidad', 'estado_docente', 'id_antiguo')
            
            print("Iniciando carga masiva en tbl_docentes...")
            postgres_cursor.copy_expert(f"COPY public.tbl_docentes ({', '.join(cols_docentes)}) FROM STDIN WITH CSV DELIMITER AS E'\t'", buffer_docentes)
            print("Carga masiva en tbl_docentes completada.")
        else:
            print("Etapa 2: No hay docentes para insertar.")

        postgres_conn.commit()
        print("Migración combinada completada exitosamente.")

    except (Exception, psycopg2.Error, mysql.connector.Error) as e:
        print(f"Error durante la migración combinada: {e}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if mysql_conn: mysql_conn.close()
        if postgres_conn: postgres_conn.close()
        print("--- Migración combinada de Usuarios y Docentes finalizada ---")

if __name__ == '__main__':
    migrate_usuarios_y_docentes_fast()
