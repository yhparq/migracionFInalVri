import psycopg2
import sys
import os
import io
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_docentes_lineas():
    """
    Migra las líneas de investigación de los docentes desde docLineas (MySQL)
    a tbl_docentes_lineas (PostgreSQL).

    Lógica de Negocio:
    - Solo se migran las filas donde el 'Estado' en MySQL es igual a 2.
    - El campo 'tipo' en PostgreSQL se establece en 1 por defecto.
    - Se mapea el IdDocente antiguo al nuevo id de la tabla tbl_docentes.
    """
    print("--- Iniciando migración de tbl_docentes_lineas ---")
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()

        if pg_conn is None or mysql_conn is None:
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur = mysql_conn.cursor(dictionary=True)

        # 1. Crear mapa de docentes: {id_antiguo: id_nuevo}
        print("  Paso 1: Creando mapa de traducción para docentes...")
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docentes_map = {row[1]: row[0] for row in pg_cur.fetchall()}
        print(f"  Se mapearon {len(docentes_map)} docentes.")

        # 2. Leer solo los registros relevantes de docLineas (Estado = 2)
        print("  Paso 2: Leyendo datos de origen desde docLineas (MySQL)...")
        mysql_cur.execute("SELECT IdDocente, IdLinea, Tipo, Estado FROM docLineas WHERE Estado = 2")
        source_data = mysql_cur.fetchall()
        print(f"  Se encontraron {len(source_data)} registros con Estado = 2 para migrar.")

        # 3. Procesar y transformar los datos
        print("  Paso 3: Procesando y transformando datos...")
        data_for_copy = []
        unmatched_docentes = 0

        for row in source_data:
            id_docente_antiguo = row['IdDocente']
            new_docente_id = docentes_map.get(id_docente_antiguo)

            if not new_docente_id:
                unmatched_docentes += 1
                continue

            data_for_copy.append((
                new_docente_id,
                row['IdLinea'],
                1,  # tipo (valor fijo)
                row['Estado'] # id_estado_linea
            ))

        print(f"  Se prepararon {len(data_for_copy)} registros para la carga masiva.")
        if unmatched_docentes > 0:
            print(f"  ADVERTENCIA: Se ignoraron {unmatched_docentes} registros por no encontrar el docente mapeado.")

        # 4. Cargar los datos en PostgreSQL usando COPY
        if data_for_copy:
            print("  Paso 4: Cargando datos en PostgreSQL con COPY...")
            buffer = io.StringIO()
            for record in data_for_copy:
                line = '\t'.join(map(str, record))
                buffer.write(line + '\n')
            
            buffer.seek(0)
            
            columns = ('id_docente', 'id_sublinea_vri', 'tipo', 'id_estado_linea')
            
            pg_cur.copy_expert(
                sql=f"COPY public.tbl_docentes_lineas ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t')",
                file=buffer
            )
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {len(data_for_copy)} registros en tbl_docentes_lineas.")

        print("--- Migración de tbl_docentes_lineas completada con éxito. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de tbl_docentes_lineas: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_docentes_lineas()
