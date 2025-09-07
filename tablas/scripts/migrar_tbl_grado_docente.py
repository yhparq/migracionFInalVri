
import os
import sys
import psycopg2

# Añadir el directorio raíz al sys.path para permitir importaciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db_connections import get_postgres_connection, get_mysql_absmain_connection

def migrate_tbl_grado_docente():
    """
    Puebla la tabla tbl_grado_docente usando IDs y una lógica optimizada.
    - Determina el grado académico más alto de cada docente desde tbl_estudios.
    - Mapea la categoría y antigüedad desde tblDocentes (MySQL).
    - Inserta los IDs correspondientes en la nueva tabla.
    """
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_absmain_connection()
        
        if not pg_conn or not mysql_conn:
            raise Exception("La conexión a la base de datos falló.")

        pg_cursor = pg_conn.cursor()
        mysql_cursor = mysql_conn.cursor(dictionary=True)

        print("--- Iniciando migración para tbl_grado_docente ---")

        # 1. Obtener jerarquía de grados académicos desde PostgreSQL
        pg_cursor.execute("SELECT id, nombre FROM dic_grados_academicos")
        grados_data = pg_cursor.fetchall()
        hierarchy = {'DOCTOR': 5, 'MAGISTER': 4, 'SEGUNDA ESPECIALIDAD': 3, 'TITULO PROFESIONAL': 2, 'BACHILLER': 1}
        grados_map = {row[0]: {'nombre': row[1], 'rank': hierarchy.get(row[1].upper(), 0)} for row in grados_data}

        # 2. Crear mapa para categorías (Nombre -> ID)
        pg_cursor.execute("SELECT id, nombre FROM dic_categoria")
        categorias_data = pg_cursor.fetchall()
        categoria_map = {row[1].upper().strip(): row[0] for row in categorias_data}
        print(f"  Se mapearon {len(categoria_map)} categorías.")

        # 3. Obtener datos de categorías antiguas desde MySQL
        mysql_cursor.execute("SELECT Codigo, Categoria, fechaasc FROM tblDocentes")
        mysql_docentes_data = {row['Codigo']: row for row in mysql_cursor.fetchall()}
        print(f"  Se obtuvieron {len(mysql_docentes_data)} registros de MySQL tblDocentes.")

        # 4. Optimización: Obtener todos los estudios de todos los docentes en una sola consulta
        pg_cursor.execute("""
            SELECT d.id as docente_id, d.id_usuario, d.codigo_airhs, es.id_grado_academico
            FROM tbl_docentes d
            JOIN tbl_estudios es ON d.id_usuario = es.id_usuario
        """)
        all_docente_studies = pg_cursor.fetchall()
        
        docentes_a_procesar = {}
        for docente_id, usuario_id, codigo_airhs, grado_id in all_docente_studies:
            if docente_id not in docentes_a_procesar:
                docentes_a_procesar[docente_id] = {
                    'usuario_id': usuario_id,
                    'codigo_airhs': codigo_airhs,
                    'grados': []
                }
            docentes_a_procesar[docente_id]['grados'].append(grado_id)
        
        print(f"  Se encontraron {len(docentes_a_procesar)} docentes con estudios para procesar.")

        records_to_insert = []
        for docente_id, data in docentes_a_procesar.items():
            
            # 5. Encontrar el grado académico más alto para el docente actual
            highest_degree_rank = -1
            highest_degree_id = None
            for degree_id in data['grados']:
                if degree_id in grados_map and grados_map[degree_id]['rank'] > highest_degree_rank:
                    highest_degree_rank = grados_map[degree_id]['rank']
                    highest_degree_id = degree_id
            
            if not highest_degree_id:
                continue

            # 6. Obtener categoría y antigüedad de los datos de MySQL
            mysql_data = mysql_docentes_data.get(data['codigo_airhs'])
            if not mysql_data or not mysql_data.get('Categoria'):
                continue

            categoria_nombre = mysql_data['Categoria'].upper().strip()
            id_categoria = categoria_map.get(categoria_nombre)
            
            if not id_categoria:
                continue

            antiguedad_categoria = mysql_data.get('fechaasc')

            records_to_insert.append((
                docente_id,
                highest_degree_id,
                id_categoria,
                antiguedad_categoria,
                1 
            ))

        # 7. Insertar todos los registros en la tabla de destino
        if records_to_insert:
            print(f"  Se prepararon {len(records_to_insert)} registros para la inserción.")
            
            insert_query = """
                INSERT INTO tbl_grado_docente (
                    id_docente, id_grado_academico, id_categoria, 
                    antiguedad_categoria, estado_tbl_grado_docente
                ) VALUES (%s, %s, %s, %s, %s)
            """
            pg_cursor.executemany(insert_query, records_to_insert)
            pg_conn.commit()
            print("--- Migración para tbl_grado_docente completada exitosamente. ---")
        else:
            print("No se encontraron registros válidos para migrar.")

    except (Exception, psycopg2.Error) as e:
        print(f"Ocurrió un error durante la migración: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("Conexiones a la base de datos cerradas.")

if __name__ == "__main__":
    migrate_tbl_grado_docente()
