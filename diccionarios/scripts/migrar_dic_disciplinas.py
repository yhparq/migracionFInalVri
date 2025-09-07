import sys
import os
import io
import csv

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_absmain_connection, get_postgres_connection

def migrate_dic_disciplinas_fast():
    """
    Migra datos de ocdeDisciplinas (MySQL) a dic_disciplinas (PostgreSQL)
    utilizando el método de carga masiva COPY.
    """
    print("--- Iniciando migración RÁPIDA de Disciplinas OCDE ---")
    
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

        # 2. Extraer y transformar datos de MySQL
        print("Extrayendo datos de 'ocdeDisciplinas' desde MySQL...")
        # Seleccionamos solo las columnas necesarias en el orden correcto para el destino
        mysql_cursor.execute("SELECT Id, IdSubArea, Nombre FROM ocdeDisciplinas;")
        source_data = mysql_cursor.fetchall()
        
        if not source_data:
            print("No hay datos para migrar.")
            return
            
        print(f"Se encontraron {len(source_data)} registros. Preparando para carga masiva.")
        
        # Añadir el valor por defecto para estado_disciplina
        transformed_data = [(row[0], row[1], row[2], 1) for row in source_data]

        # 3. Usar COPY para una carga masiva y eficiente
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter='\t', quotechar='"')
        writer.writerows(transformed_data)
        buffer.seek(0)

        print("Iniciando carga masiva con COPY en PostgreSQL...")
        
        columns = ('id', 'id_subarea', 'nombre', 'estado_disciplina')
        pg_cursor.copy_expert(f"COPY public.dic_disciplinas ({', '.join(columns)}) FROM STDIN WITH CSV DELIMITER AS E'\t'", buffer)

        # 4. Confirmar la transacción
        pg_conn.commit()
        
        print(f"¡Éxito! Se han insertado {len(transformed_data)} registros en 'dic_disciplinas' usando COPY.")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        # 5. Cerrar conexiones
        if mysql_cursor:
            mysql_cursor.close()
        if pg_cursor:
            pg_cursor.close()
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
        if pg_conn:
            pg_conn.close()
        print("--- Migración de Disciplinas OCDE finalizada ---")

if __name__ == '__main__':
    migrate_dic_disciplinas_fast()
