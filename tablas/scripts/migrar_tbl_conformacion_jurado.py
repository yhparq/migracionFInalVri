import psycopg2
import sys
import os
import io

# Ajuste del sys.path para permitir importaciones desde el directorio raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection

def migrate_tbl_conformacion_jurado_fast():
    """
    Puebla la tabla 'tbl_conformacion_jurados' a partir de los datos ya migrados
    en 'tbl_asignacion', utilizando el método COPY para mayor rendimiento.

    Esta versión está corregida para usar los nombres de columna correctos
    de 'tbl_asignacion' (ej. fecha_asignacion) y la lógica de filtrado adecuada.
    """
    print("--- Iniciando migración DEFINITIVA de tbl_conformacion_jurado (Método COPY) ---")
    pg_conn = None
    try:
        pg_conn = get_postgres_connection()
        if pg_conn is None:
            raise Exception("No se pudo conectar a la base de datos de PostgreSQL.")

        pg_cur = pg_conn.cursor()

        # PASO 1: Truncar la tabla para asegurar un estado limpio
        print("  Paso 1: Vaciando la tabla tbl_conformacion_jurados...")
        pg_cur.execute("TRUNCATE TABLE public.tbl_conformacion_jurados RESTART IDENTITY CASCADE;")
        print("  Tabla vaciada con éxito.")

        # PASO 2: Seleccionar los jurados correctos desde tbl_asignacion
        print("  Paso 2: Obteniendo jurados aceptados desde tbl_asignacion...")
        
        # Lógica de SELECT corregida: usa 'fecha_asignacion' y elimina la referencia a 'id_rol'.
        sql_select = """
        SELECT
            a.id_tramite,
            a.id_docente,
            a.orden,
            5, -- 5: Revisión de Proyecto (Etapa Fija para esta conformación)
            27653, -- ID del usuario "Sistema"
            a.id, -- El ID de la tabla de asignación, como se requiere
            a.fecha_asignacion, -- La fecha en que el jurado fue asignado
            1 -- 1: Activo
        FROM
            public.tbl_asignacion a
        WHERE
            a.estado_asignacion = 1; -- 1: Aceptado
        """
        
        pg_cur.execute(sql_select)
        source_data = pg_cur.fetchall()
        
        print(f"  Se obtuvieron {len(source_data)} registros de jurados para procesar.")

        # PASO 3: Preparar los datos y cargarlos con COPY
        if source_data:
            print("  Paso 3: Cargando datos en PostgreSQL con COPY...")
            
            buffer = io.StringIO()
            for record in source_data:
                line = '\t'.join(str(item) if item is not None else '\\N' for item in record)
                buffer.write(line + '\n')
            
            buffer.seek(0)

            columns = (
                'id_tramite', 'id_docente', 'orden', 'id_etapa', 
                'id_usuario_asignador', 'id_asignacion', 'fecha_asignacion', 'estado_cj'
            )
            
            pg_cur.copy_expert(
                sql=f"COPY public.tbl_conformacion_jurados ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')",
                file=buffer
            )
            
            pg_conn.commit()
            print(f"  Carga masiva completada. Se insertaron {len(source_data)} registros.")
        else:
            print("  No se encontraron jurados aceptados para migrar.")

        print("--- Migración DEFINITIVA de tbl_conformacion_jurado completada con éxito ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de conformación de jurados: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        print("--- Conexión a PostgreSQL cerrada ---")

if __name__ == '__main__':
    migrate_tbl_conformacion_jurado_fast()