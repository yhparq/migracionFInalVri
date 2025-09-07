import psycopg2
import sys
import os
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

# Añadir el directorio raíz al sys.path para importar db_connections
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_dictamenes_sustentaciones():
    """
    Puebla tbl_dictamenes_info con datos de sustentaciones (tesSustenAct).
    - No borra registros existentes.
    - La lógica de aprobación se basa en el campo 'Obs'.
    - El folio se mapea desde el ID de tesSustenAct.
    - CORREGIDO: Obtiene el título desde tesTramsDet para evitar errores.
    """
    print("--- Iniciando migración de sustentaciones para poblar tbl_dictamenes_info (v2 CORREGIDA) ---")
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()

        if pg_conn is None or mysql_conn is None:
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur = mysql_conn.cursor(dictionary=True)

        # 1. Crear mapas de traducción
        print("  Paso 1: Creando mapas de traducción y búsqueda...")
        
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        tramites_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docentes_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id, CONCAT(nombres, ' ', apellidos) as full_name FROM tbl_usuarios")
        usuarios_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id, nombre FROM dic_carreras")
        carreras_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id_antiguo, id_usuario FROM tbl_tesistas WHERE id_antiguo IS NOT NULL")
        tesistas_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        # CORRECCIÓN: Se quita 'Titulo' de esta consulta.
        mysql_cur.execute("SELECT Id, Codigo, IdTesista1, IdTesista2, IdCarrera, IdJurado1, IdJurado2, IdJurado3, IdJurado4 FROM tesTramites")
        tes_tramites_map = {row['Id']: row for row in mysql_cur.fetchall()}
        
        # CORRECCIÓN: Se crea un mapa específico para los títulos desde tesTramsDet
        # Se asume que el título no cambia, por lo que se agrupa por IdTramite y se toma el primero.
        mysql_cur.execute("SELECT IdTramite, Titulo FROM tesTramsDet WHERE Titulo IS NOT NULL AND Titulo != '' GROUP BY IdTramite, Titulo")
        titulos_map = {row['IdTramite']: row['Titulo'] for row in mysql_cur.fetchall()}

        print(f"  Mapeos completados.")

        # 2. Consulta principal: Obtener datos de sustentaciones
        print("  Paso 2: Obteniendo datos de sustentaciones desde MySQL (tesSustenAct)...")
        mysql_cur.execute("SELECT Id, IdTramite, Fecha, Obs FROM tesSustenAct")
        source_sustentaciones = mysql_cur.fetchall()
        total_source = len(source_sustentaciones)
        print(f"  Se encontraron {total_source} registros de sustentación para procesar.")

        # 3. Procesar y transformar los datos
        print("  Paso 3: Procesando y transformando datos...")
        records_to_insert = []
        omitted_count = 0
        
        for sus in source_sustentaciones:
            id_tramite_antiguo = sus['IdTramite']
            id_sustentacion_antiguo = sus['Id']

            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            if not new_tramite_id:
                print(f"    [OMITIDO] Sustentación ID {id_sustentacion_antiguo}: No se encontró el nuevo ID para el Trámite antiguo ID {id_tramite_antiguo}.")
                omitted_count += 1
                continue

            tramite_info = tes_tramites_map.get(id_tramite_antiguo)
            if not tramite_info:
                print(f"    [OMITIDO] Sustentación ID {id_sustentacion_antiguo}: No se encontró info en 'tesTramites' para el Trámite antiguo ID {id_tramite_antiguo}.")
                omitted_count += 1
                continue

            obs_text = (sus.get('Obs') or "").strip().upper()
            tipo_aprobacion_id = None
            if "DESAPROBADO" in obs_text:
                tipo_aprobacion_id = 32
            elif obs_text == "APROBADO":
                tipo_aprobacion_id = 30
            elif "APROBADO" in obs_text:
                tipo_aprobacion_id = 31
            
            if tipo_aprobacion_id is None:
                print(f"    [OMITIDO] Sustentación ID {id_sustentacion_antiguo}: No se pudo determinar el tipo de aprobación para Obs='{sus.get('Obs')}'")
                omitted_count += 1
                continue

            def get_user_name(id_antiguo, map_type, role):
                if not id_antiguo: return 'N/A' if map_type == 'docente' else None
                new_id = docentes_map.get(id_antiguo) if map_type == 'docente' else tesistas_map.get(id_antiguo)
                if not new_id:
                    print(f"    [ADVERTENCIA] Trámite ID {id_tramite_antiguo}: No se encontró nuevo ID de {map_type} para el antiguo ID {id_antiguo} ({role}).")
                    return 'N/A'
                return usuarios_map.get(new_id, 'N/A')

            presidente = get_user_name(tramite_info.get('IdJurado1'), 'docente', 'Presidente')
            primer_miembro = get_user_name(tramite_info.get('IdJurado2'), 'docente', '1er Miembro')
            segundo_miembro = get_user_name(tramite_info.get('IdJurado3'), 'docente', '2do Miembro')
            asesor = get_user_name(tramite_info.get('IdJurado4'), 'docente', 'Asesor')
            tesista1 = get_user_name(tramite_info.get('IdTesista1'), 'tesista', 'Tesista 1')
            tesista2 = get_user_name(tramite_info.get('IdTesista2'), 'tesista', 'Tesista 2')
            escuela_profesional = carreras_map.get(tramite_info.get('IdCarrera'), 'N/A')
            
            # CORRECCIÓN: Obtener título del mapa de títulos
            titulo = titulos_map.get(id_tramite_antiguo, 'Título no encontrado')

            record = (
                new_tramite_id,
                tramite_info.get('Codigo'),
                tipo_aprobacion_id,
                titulo,
                tesista1,
                tesista2,
                escuela_profesional,
                presidente,
                primer_miembro,
                segundo_miembro,
                asesor,
                None, # coasesor
                sus.get('Fecha'),
                None, # token
                1, # estado
                2, # tipo_acta
                id_sustentacion_antiguo # folio
            )
            records_to_insert.append(record)

        print(f"\n  Resumen del procesamiento: {total_source} registros leídos, {len(records_to_insert)} preparados para inserción, {omitted_count} omitidos.")

        if records_to_insert:
            print("  Paso 4: Insertando datos de sustentaciones en tbl_dictamenes_info...")
            insert_query = """
                INSERT INTO tbl_dictamenes_info (
                    id_tramite, codigo_proyecto, tipo_aprobacion, titulo, tesista1, tesista2,
                    escuela_profesional, presidente, primer_miembro, segundo_miembro, asesor,
                    coasesor, fecha_dictamen, token, estado, tipo_acta, folio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            pg_cur.executemany(insert_query, records_to_insert)
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {pg_cur.rowcount} registros nuevos.")

        print("--- Migración de sustentaciones para tbl_dictamenes_info completada. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de sustentaciones: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_dictamenes_sustentaciones()