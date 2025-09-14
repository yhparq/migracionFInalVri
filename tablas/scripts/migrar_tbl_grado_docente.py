import os
import sys
import psycopg2
from collections import defaultdict

# Add parent directory to Python path to allow module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection, get_mysql_absmain_connection

def migrate_tbl_grado_docente():
    """
    Populates the tbl_grado_docente table by efficiently combining data from 
    PostgreSQL (tbl_docentes, tbl_estudios) and MySQL (tblDocentes) using in-memory maps.
    """
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_absmain_connection()
        
        if not pg_conn or not mysql_conn:
            raise Exception("Database connection failed.")

        pg_cursor = pg_conn.cursor()
        mysql_cursor = mysql_conn.cursor(dictionary=True)

        print("--- Iniciando migración para tbl_grado_docente ---")

        # 1. Cargar mapas de traducción y datos necesarios en memoria
        print("INFO: Cargando datos en memoria para un procesamiento eficiente...")

        # Mapa de Grados Académicos con su jerarquía
        pg_cursor.execute("SELECT id, nombre FROM dic_grados_academicos")
        hierarchy = {'Doctor': 5, 'Magíster': 4, 'Segunda Especialidad': 3, 'Título Profesional': 2, 'Bachiller': 1}
        grados_map = {row[0]: {'nombre': row[1], 'rank': hierarchy.get(row[1], 0)} for row in pg_cursor.fetchall()}

        # Mapa de Docentes Nuevos: id_antiguo -> (nuevo_docente_id, nuevo_usuario_id)
        pg_cursor.execute("SELECT id, id_usuario, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        mapa_docentes_nuevos = {row[2]: (row[0], row[1]) for row in pg_cursor.fetchall()}

        # Mapa de Estudios por Usuario: id_usuario -> [lista_de_ids_de_grado]
        pg_cursor.execute("SELECT id_usuario, id_grado_academico FROM tbl_estudios")
        estudios_por_usuario = defaultdict(list)
        for id_usuario, id_grado_academico in pg_cursor.fetchall():
            estudios_por_usuario[id_usuario].append(id_grado_academico)

        # 2. Obtener todos los docentes de la tabla antigua de MySQL
        mysql_cursor.execute("SELECT Id, IdCategoria, FechaAsc FROM tblDocentes")
        docentes_antiguos = mysql_cursor.fetchall()
        print(f"INFO: Se encontraron {len(docentes_antiguos)} registros en MySQL para procesar.")

        final_records = {}
        docentes_no_encontrados = 0

        # 3. Procesar cada docente antiguo en memoria, manejando duplicados
        for docente_antiguo in docentes_antiguos:
            id_antiguo_mysql = docente_antiguo['Id']
            
            # Buscar el docente en el mapa de nuevos docentes usando el ID antiguo
            if id_antiguo_mysql not in mapa_docentes_nuevos:
                docentes_no_encontrados += 1
                continue
            
            docente_id, usuario_id = mapa_docentes_nuevos[id_antiguo_mysql]
            
            # Si el usuario no tiene estudios, no podemos determinar su grado
            if usuario_id not in estudios_por_usuario:
                continue

            # Calcular el grado más alto para el usuario
            highest_degree_rank = -1
            highest_degree_id = None
            for degree_id in estudios_por_usuario[usuario_id]:
                if degree_id in grados_map and grados_map[degree_id]['rank'] > highest_degree_rank:
                    highest_degree_rank = grados_map[degree_id]['rank']
                    highest_degree_id = degree_id
            
            if not highest_degree_id:
                continue

            # Lógica para manejar duplicados: solo conservar el registro con el grado más alto.
            # Si el docente ya existe en `final_records`, se compara su grado actual con el nuevo.
            if docente_id in final_records:
                # Obtener el rank del grado ya almacenado
                existing_degree_id = final_records[docente_id][1] # El id del grado está en el índice 1
                existing_rank = grados_map.get(existing_degree_id, {}).get('rank', -1)
                if highest_degree_rank <= existing_rank:
                    continue # El grado existente es mayor o igual, no hacer nada

            # Almacenar o actualizar el registro del docente con su grado más alto
            final_records[docente_id] = (
                docente_id,
                highest_degree_id,  # Usar el ID del grado, no el nombre
                docente_antiguo.get('IdCategoria'),
                docente_antiguo.get('FechaAsc'),
                1  # estado_tbl_grado_docente (smallint)
            )
        
        records_to_insert = list(final_records.values())

        print(f"INFO: Procesamiento finalizado. {len(records_to_insert)} registros válidos para insertar.")
        if docentes_no_encontrados > 0:
            print(f"WARN: Se omitieron {docentes_no_encontrados} docentes de MySQL porque no se encontraron en la nueva base de datos.")

        # 4. Insertar todos los registros en bloque
        if records_to_insert:
            print("INFO: Vaciando la tabla de destino y realizando la inserción masiva...")
            pg_cursor.execute("TRUNCATE TABLE public.tbl_grado_docente RESTART IDENTITY CASCADE;")
            
            insert_query = """
                INSERT INTO tbl_grado_docente (
                    id_docente, id_grado_academico, id_categoria, 
                    antiguedad_categoria, estado_tbl_grado_docente
                ) VALUES (%s, %s, %s, %s, %s)
            """
            pg_cursor.executemany(insert_query, records_to_insert)
            pg_conn.commit()
            print(f"--- Migración para tbl_grado_docente completada exitosamente. Se insertaron {pg_cursor.rowcount} registros. ---")
        else:
            print("--- No se encontraron registros válidos para migrar. ---")

    except (Exception, psycopg2.Error) as e:
        print(f"ERROR: Ocurrió un error durante la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("INFO: Conexiones a la base de datos cerradas.")

if __name__ == "__main__":
    migrate_tbl_grado_docente()