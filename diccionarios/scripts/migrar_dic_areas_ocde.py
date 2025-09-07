import sys
import os
import io
import csv

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_absmain_connection, get_postgres_connection

def migrate_dic_areas_ocde_fast():
    """
    Migra datos de ocdeAreas (MySQL) a dic_areas_ocde (PostgreSQL) utilizando
    el método de carga masiva COPY para un rendimiento óptimo.
    """
    print("--- Iniciando migración RÁPIDA de Áreas OCDE ---")
    
    pg_conn = None
    mysql_conn = None
    
    try:
        # 1. Establecer conexiones
        mysql_conn = get_mysql_absmain_connection()
        pg_conn = get_postgres_connection()

        if not mysql_conn or not pg_conn:
            raise Exception("No se pudieron establecer las conexiones a la base de datos.")

        pg_cursor = pg_conn.cursor()
        mysql_cursor = mysql_conn.cursor()

        # La limpieza de la tabla ahora es manejada por el orquestador principal (run_migrate.py)

        # 3. Extraer y transformar datos de MySQL
        print("Extrayendo datos de 'ocdeAreas' desde MySQL...")
        mysql_cursor.execute("SELECT Id, Nombre FROM ocdeAreas;")
        source_data = mysql_cursor.fetchall()
        
        if not source_data:
            print("No hay datos para migrar.")
            return
            
        print(f"Se encontraron {len(source_data)} registros. Preparando para carga masiva.")
        
        # Añadir el valor por defecto para estado_area
        transformed_data = [(row[0], row[1], 1) for row in source_data]

        # 4. Usar COPY para una carga masiva y eficiente
        # Creamos un buffer en memoria para actuar como un archivo CSV
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter='\t', quotechar='"')
        writer.writerows(transformed_data)
        buffer.seek(0) # Rebobinamos el buffer al principio

        print("Iniciando carga masiva con COPY en PostgreSQL...")
        
        # Definimos las columnas explícitamente
        columns = ('id', 'nombre', 'estado_area')
        pg_cursor.copy_expert(f"COPY public.dic_areas_ocde ({', '.join(columns)}) FROM STDIN WITH CSV DELIMITER AS E'\t'", buffer)

        # 5. Confirmar la transacción
        pg_conn.commit()
        
        print(f"¡Éxito! Se han insertado {len(transformed_data)} registros en 'dic_areas_ocde' usando COPY.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        # 6. Cerrar conexiones
        if mysql_cursor:
            mysql_cursor.close()
        if pg_cursor:
            pg_cursor.close()
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
        if pg_conn:
            pg_conn.close()
        print("--- Migración de Áreas OCDE finalizada ---")

if __name__ == '__main__':
    migrate_dic_areas_ocde_fast()
