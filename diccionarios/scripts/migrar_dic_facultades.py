import sys
import os
import io
import csv

# Añadir el directorio raíz al sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_mysql_absmain_connection, get_postgres_connection

def migrate_dic_facultades_fast():
    """
    Migra datos de dicFacultades (MySQL) a dic_facultades (PostgreSQL)
    utilizando el método de carga masiva COPY.
    
    Excluye el registro con Id = 20 para evitar errores de clave foránea.
    """
    print("--- Iniciando migración RÁPIDA de Facultades ---")
    
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

        # 2. Extraer y transformar datos de MySQL, excluyendo el registro problemático
        print("Extrayendo datos de 'dicFacultades' desde MySQL (excluyendo Id=20)...")
        mysql_cursor.execute("SELECT Id, Nombre, Abrev, IdArea FROM dicFacultades WHERE Id != 20;")
        source_data = mysql_cursor.fetchall()
        
        if not source_data:
            print("No hay datos para migrar.")
            return
            
        print(f"Se encontraron {len(source_data)} registros. Preparando para carga masiva.")
        
        # Añadir el valor por defecto para estado_facultad
        transformed_data = [(row[0], row[1], row[2], row[3], 1) for row in source_data]

        # 3. Usar COPY para una carga masiva y eficiente
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter='\t', quotechar='"')
        writer.writerows(transformed_data)
        buffer.seek(0)

        print("Iniciando carga masiva con COPY en PostgreSQL...")
        
        columns = ('id', 'nombre', 'abreviatura', 'id_area', 'estado_facultad')
        pg_cursor.copy_expert(f"COPY public.dic_facultades ({', '.join(columns)}) FROM STDIN WITH CSV DELIMITER AS E'\t'", buffer)

        # 4. Confirmar la transacción
        pg_conn.commit()
        
        print(f"¡Éxito! Se han insertado {len(transformed_data)} registros en 'dic_facultades' usando COPY.")

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
        print("--- Migración de Facultades finalizada ---")

if __name__ == '__main__':
    migrate_dic_facultades_fast()
