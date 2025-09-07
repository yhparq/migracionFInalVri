import sys
import os
import io
import csv
import psycopg2
import mysql.connector

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_absmain_connection, get_postgres_connection

def migrate_tbl_sublineas_vri_fast():
    """
    Migra datos de tblLineas (MySQL) a tbl_sublineas_vri (PostgreSQL)
    utilizando el método de carga masiva COPY.
    """
    print("--- Iniciando migración RÁPIDA de Sublíneas VRI ---")
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

        # 2. Extraer y transformar datos de MySQL
        print("Extrayendo datos de 'tblLineas' desde MySQL...")
        mysql_cursor.execute("SELECT Id, id_lineaV, Nombre, IdDiscip, IdCarrera, fecha, Estado FROM tblLineas;")
        source_data = mysql_cursor.fetchall()
        
        if not source_data:
            print("No hay datos para migrar.")
            return
            
        print(f"Se encontraron {len(source_data)} registros. Preparando para carga masiva.")
        
        # 3. Preparar los datos para la inserción, duplicando la fecha
        transformed_data = []
        for row in source_data:
            transformed_data.append([
                row['Id'],
                row['id_lineaV'],
                row['Nombre'],
                row['IdDiscip'],
                row['IdCarrera'],
                row['fecha'],      # fecha_registro
                row['fecha'],      # fecha_modificacion
                row['Estado']
            ])

        # 4. Usar COPY para una carga masiva y eficiente
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter='\t', quotechar='"')
        writer.writerows(transformed_data)
        buffer.seek(0)

        print("Iniciando carga masiva con COPY en PostgreSQL...")
        
        columns = ('id', 'id_linea_universidad', 'nombre', 'id_disciplina', 'id_carrera', 'fecha_registro', 'fecha_modificacion', 'estado_sublinea_vri')
        postgres_cursor.copy_expert(f"COPY public.tbl_sublineas_vri ({', '.join(columns)}) FROM STDIN WITH CSV DELIMITER AS E'\t'", buffer)

        postgres_conn.commit()
        
        print(f"¡Éxito! Se han insertado {len(transformed_data)} registros en 'tbl_sublineas_vri' usando COPY.")

    except (Exception, psycopg2.Error, mysql.connector.Error) as e:
        print(f"Error durante la migración de Sublíneas VRI: {e}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if mysql_conn:
            mysql_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("--- Migración de Sublíneas VRI finalizada ---")

if __name__ == '__main__':
    migrate_tbl_sublineas_vri_fast()
