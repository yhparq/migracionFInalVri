import io
import os
import sys
import psycopg2
import mysql.connector
import pandas as pd

# Ajuste del sys.path para permitir importaciones desde el directorio raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_mysql_pilar3_connection, get_postgres_connection

def migrate_tbl_tramites_fast():
    """
    Migra datos de tesTramites (MySQL) a tbl_tramites (PostgreSQL) de forma optimizada
    utilizando el método COPY de PostgreSQL para una carga masiva de alto rendimiento.

    Lógica de Mapeo:
    - Se migran todos los trámites para no perder datos.
    - 'Estado' (MySQL) se mapea a 'id_etapa' (PostgreSQL) usando un diccionario.
    - Si un 'Estado' no tiene mapeo, se le asigna un id_etapa por defecto (1).
    - 'id_tipo_trabajo' se establece en 1 por defecto.
    - 'id_modalidad' se toma del campo 'Tipo'.
    - 'estado_tramite' se basa en 'SuEst' (1 = activo, otro = inactivo).
    - No se ejecuta TRUNCATE, asumiendo que el script orquestador lo maneja.
    """
    mysql_conn = None
    postgres_conn = None
    
    try:
        # Establecer conexiones
        mysql_conn = get_mysql_pilar3_connection()
        postgres_conn = get_postgres_connection()
        if not all([mysql_conn, postgres_conn]):
            print("Error: No se pudieron establecer las conexiones a la base de datos.")
            return

        print("Conexiones a MySQL y PostgreSQL establecidas correctamente.")
        
        # 1. Extracción de datos desde MySQL
        sql_query = "SELECT Id, Codigo, Estado, IdLinea, Tipo, FechRegProy, SuEst FROM tesTramites"
        df = pd.read_sql(sql_query, mysql_conn)
        print(f"Se extrajeron {len(df)} registros de tesTramites (MySQL).")

        # 2. Transformación y Mapeo de datos con Pandas
        print("Iniciando transformación de datos...")
        
        etapa_map = {
            0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 3, 6: 4, 7: 5,
            8: 8, 9: 10, 10: 11, 11: 11, 12: 12, 13: 13, 14: 14
        }
        ID_ETAPA_DEFAULT = 1

        df['id_etapa'] = df['Estado'].map(etapa_map).fillna(ID_ETAPA_DEFAULT).astype(int)
        # El estado del trámite se define por el campo 'Tipo': 0 o menos es inactivo (0), 1 o más es activo (1).
        df['estado_tramite'] = df['Tipo'].apply(lambda x: 1 if x >= 1 else 0).astype(int)
        
        # Mapeo seguro para id_modalidad: si no es 1, usar 1 como default.
        df['Tipo'] = df['Tipo'].apply(lambda x: 1 if x == 1 else 1).astype(int)

        # Creación de las columnas restantes
        df['id_tipo_trabajo'] = 1
        df['id_denominacion'] = 1  # Placeholder, requiere mapeo complejo posterior

        # Renombrar y seleccionar las columnas en el orden correcto para PostgreSQL
        df.rename(columns={
            'Id': 'id_antiguo',
            'Codigo': 'codigo_proyecto',
            'IdLinea': 'id_sublinea_vri',
            'Tipo': 'id_modalidad',
            'FechRegProy': 'fecha_registro'
        }, inplace=True)

        # Asegurar el orden de las columnas para el COPY
        df_final = df[[
            'id_antiguo', 'codigo_proyecto', 'id_etapa', 'id_sublinea_vri', 
            'id_modalidad', 'id_tipo_trabajo', 'id_denominacion', 
            'fecha_registro', 'estado_tramite'
        ]]
        print("Transformación de datos completada.")

        # 3. Carga de datos a PostgreSQL usando COPY
        print("Iniciando carga de datos a PostgreSQL con el método COPY...")
        
        # Crear un buffer en memoria para no escribir en disco
        buffer = io.StringIO()
        df_final.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
        buffer.seek(0) # Rebobinar el buffer al principio

        postgres_cursor = postgres_conn.cursor()
        
        # Ejecutar el comando COPY
        postgres_cursor.copy_expert(
            sql=r"""
                COPY public.tbl_tramites (
                    id_antiguo, codigo_proyecto, id_etapa, id_sublinea_vri, id_modalidad,
                    id_tipo_trabajo, id_denominacion, fecha_registro, estado_tramite
                ) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')
            """,
            file=buffer
        )
        
        postgres_conn.commit()
        print(f"Carga masiva completada. Se han migrado {len(df_final)} registros a tbl_tramites.")

    except (Exception, psycopg2.Error, mysql.connector.Error) as e:
        print(f"Error catastrófico durante la migración de tbl_tramites: {e}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()
            print("Conexión a MySQL cerrada.")
        if postgres_conn:
            postgres_conn.close()
            print("Conexión a PostgreSQL cerrada.")

if __name__ == "__main__":
    # Para ejecutar este script, asegúrate de tener pandas instalado:
    # pip install pandas
    migrate_tbl_tramites_fast()
