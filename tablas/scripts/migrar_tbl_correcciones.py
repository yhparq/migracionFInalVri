
import psycopg2
import sys
import os
import io
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

        # 2. Crear mapa de búsqueda para la conformación de jurados
        print("  Paso 2: Creando mapa de búsqueda para la conformación de jurados...")
        pg_cur.execute("SELECT id, id_tramite, id_docente, id_orden FROM tbl_conformacion_jurados")
        conformacion_map = {(row[1], row[2]): (row[0], row[3]) for row in pg_cur.fetchall()}
        print(f"  Se mapearon {len(conformacion_map)} registros de conformación para búsqueda.")

        # 3. Leer correcciones de la tabla de origen en MySQL (tesCorrects)
        print("  Paso 3: Leyendo correcciones desde MySQL (tesCorrects)...")
        mysql_cur.execute("SELECT IdTramite, IdDocente, Fecha, Mensaje, Iteracion FROM tblCorrects")
        source_correcciones = mysql_cur.fetchall()
        print(f"  Se encontraron {len(source_correcciones)} correcciones en origen.")

        # 4. Preparar datos para la inserción, aplicando la lógica de negocio
        print("  Paso 4: Procesando y transformando datos...")
        data_for_copy = []
        unmatched_count = 0
        unmatched_log = []

        for corr in source_correcciones:
            id_tramite_antiguo = corr['IdTramite']
            id_docente_antiguo = corr['IdDocente']
            iteracion = corr['Iteracion']

            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            new_docente_id = docente_map.get(id_docente_antiguo)

            if not new_tramite_id or not new_docente_id:
                unmatched_count += 1
                unmatched_log.append(f"  - Razón: No se encontró mapeo de ID para Trámite Antiguo '{id_tramite_antiguo}' o Docente Antiguo '{id_docente_antiguo}'.")
                continue

            match = conformacion_map.get((new_tramite_id, new_docente_id))
            
            if not match:
                unmatched_count += 1
                unmatched_log.append(f"  - Razón: No se encontró registro de conformación para Trámite Nuevo '{new_tramite_id}' y Docente Nuevo '{new_docente_id}'.")
                continue

            id_conformacion_jurado, id_orden = match

            id_etapa = None
            if iteracion == 1:
                id_etapa = 6
            elif iteracion in [2, 3]:
                id_etapa = 7
            elif iteracion == 4:
                id_etapa = 12
            
            if id_etapa is None:
                unmatched_count += 1
                unmatched_log.append(f"  - Razón: Iteración '{iteracion}' no mapea a una etapa válida para Trámite Antiguo '{id_tramite_antiguo}'.")
                continue

            data_for_copy.append(
                (id_conformacion_jurado, id_orden, corr['Mensaje'], 
                 corr['Fecha'], 1, id_etapa)
            )
        
        print(f"  Se prepararon {len(data_for_copy)} correcciones para la carga masiva.")
        if unmatched_count > 0:
            print(f"  Se ignoraron {unmatched_count} correcciones.")
            # (Opcional: imprimir logs si es necesario para depuración)

        # 5. Cargar los datos en PostgreSQL usando el método COPY
        if data_for_copy:
            print("  Paso 5: Cargando datos en PostgreSQL con COPY...")
            buffer = io.StringIO()
            for record in data_for_copy:
                # Limpiar saltos de línea y tabulaciones en el mensaje para no romper el formato CSV
                mensaje_limpio = str(record[2]).replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                
                # Reconstruir la tupla con el mensaje limpio
                clean_record = (record[0], record[1], mensaje_limpio, record[3], record[4], record[5])
                
                line = '\t'.join(str(item) if item is not None else '\\N' for item in clean_record)
                buffer.write(line + '\n')
            
            buffer.seek(0)

            # OJO: "Fecha_correccion" va entre comillas dobles porque es case-sensitive en PostgreSQL
            columns = (
                'id_conformacion_jurado', 'orden', 'mensaje_correccion', 
                '"Fecha_correccion"', 'estado_correccion', 'id_etapa'
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
