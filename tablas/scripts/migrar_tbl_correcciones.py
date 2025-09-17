
import psycopg2
import sys
import os
import io
import csv
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

# Ajuste del sys.path para permitir importaciones desde el directorio raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_correcciones_jurados():
    """
    Migra las correcciones de jurados desde tesCorrects (MySQL), mapeando
    IDs antiguos a nuevos y asignando la etapa según la iteración.
    Utiliza el método COPY para una carga masiva eficiente.
    """
    print("--- Iniciando migración de tbl_correcciones_jurados (Método COPY) ---")
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()

        if pg_conn is None or mysql_conn is None:
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur = mysql_conn.cursor(dictionary=True)

        # 1. Crear mapas para traducir IDs antiguos a nuevos desde PostgreSQL
        print("  Paso 1: Creando mapas de IDs desde PostgreSQL...")
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docente_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        tramites_map = {row[1]: row[0] for row in pg_cur.fetchall()}
        print(f"  Mapeo inicial completado: {len(docente_map)} docentes, {len(tramites_map)} trámites.")

        # 2. Leer correcciones de la tabla de origen en MySQL (tesCorrects)
        print("  Paso 2: Leyendo correcciones desde MySQL (tblCorrects)...")
        mysql_cur.execute("SELECT IdTramite, IdDocente, Fecha, Mensaje, Iteracion FROM tblCorrects")
        source_correcciones = mysql_cur.fetchall()
        print(f"  Se encontraron {len(source_correcciones)} correcciones en origen.")

        # 3. Preparar datos para la inserción, aplicando la lógica de negocio
        print("  Paso 3: Procesando y transformando datos...")
        data_for_copy = []
        unmatched_count = 0
        
        for corr in source_correcciones:
            id_tramite_antiguo = corr['IdTramite']
            id_docente_antiguo = corr['IdDocente']
            iteracion = corr['Iteracion']

            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            new_docente_id = docente_map.get(id_docente_antiguo)

            if not new_tramite_id or not new_docente_id:
                unmatched_count += 1
                continue

            id_etapa = None
            if iteracion == 1: id_etapa = 6
            elif iteracion in [2, 3]: id_etapa = 7
            elif iteracion == 4: id_etapa = 12
            
            if id_etapa is None:
                unmatched_count += 1
                continue

            mensaje_limpio = str(corr['Mensaje']).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')

            data_for_copy.append(
                (new_tramite_id, new_docente_id, id_etapa, mensaje_limpio, 
                 corr['Fecha'], 1)
            )
        
        print(f"  Se prepararon {len(data_for_copy)} correcciones para la carga masiva.")
        if unmatched_count > 0:
            print(f"  Se ignoraron {unmatched_count} correcciones por falta de mapeo o etapa inválida.")

        # 4. Cargar los datos en PostgreSQL usando el método COPY
        if data_for_copy:
            print("  Paso 4: Cargando datos en PostgreSQL con COPY...")
            buffer = io.StringIO()
            writer = csv.writer(buffer, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(data_for_copy)
            buffer.seek(0)

            columns = (
                'id_tramite', 'id_docente', 'id_etapa', 'mensaje_correccion', 
                'fecha_correccion', 'estado_correccion'
            )
            
            pg_cur.copy_expert(
                sql=f"COPY public.tbl_correcciones_jurados ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\t', NULL '\\N')",
                file=buffer
            )
            
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {len(data_for_copy)} registros en tbl_correcciones_jurados.")

        print("--- Migración de tbl_correcciones_jurados completada con éxito. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de correcciones: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_correcciones_jurados()
