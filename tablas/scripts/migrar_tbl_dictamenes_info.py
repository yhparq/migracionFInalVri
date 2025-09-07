import psycopg2
import sys
import os
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_dictamenes_info():
    """
    VERSIÓN MEJORADA: Puebla la tabla tbl_dictamenes_info consolidando datos.
    - tipo_aprobacion es un INTEGER mapeado a dic_acciones.
    - Incluye valores por defecto para 'tipo_acta' y 'folio'.
    - Añade logging detallado para identificar registros omitidos o con datos faltantes.
    """
    print("--- Iniciando migración MEJORADA para poblar tbl_dictamenes_info ---")
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()

        if pg_conn is None or mysql_conn is None:
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur = mysql_conn.cursor(dictionary=True)

        # 1. Crear todos los mapas necesarios en memoria para eficiencia
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

        mysql_cur.execute("SELECT Id, Codigo, IdTesista1, IdTesista2, IdCarrera, IdJurado1, IdJurado2, IdJurado3, IdJurado4 FROM tesTramites")
        tes_tramites_map = {row['Id']: row for row in mysql_cur.fetchall()}
        
        print(f"  Mapeos completados: {len(tramites_map)} trámites, {len(docentes_map)} docentes, {len(tesistas_map)} tesistas.")

        # 2. Consulta principal: Obtener los dictámenes de Iteración 3
        print("  Paso 2: Obteniendo dictámenes de Iteración 3 desde MySQL...")
        mysql_cur.execute("SELECT Id, IdTramite, Titulo, vb1, vb2, vb3, Fecha FROM tesTramsDet WHERE Iteracion = 3")
        source_dictamenes = mysql_cur.fetchall()
        total_source = len(source_dictamenes)
        print(f"  Se encontraron {total_source} dictámenes para procesar.")

        # 3. Procesar y transformar los datos
        print("  Paso 3: Procesando y transformando datos...")
        records_to_insert = []
        omitted_count = 0
        
        for idx, det in enumerate(source_dictamenes):
            id_tramite_antiguo = det['IdTramite']
            id_detalle_antiguo = det['Id']

            # --- Verificación de Trámite ---
            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            if not new_tramite_id:
                print(f"    [OMITIDO] Dictamen Detalle ID {id_detalle_antiguo}: No se encontró el nuevo ID para el Trámite antiguo ID {id_tramite_antiguo}.")
                omitted_count += 1
                continue

            tramite_info = tes_tramites_map.get(id_tramite_antiguo)
            if not tramite_info:
                print(f"    [OMITIDO] Dictamen Detalle ID {id_detalle_antiguo}: No se encontró información de 'tesTramites' para el Trámite antiguo ID {id_tramite_antiguo}.")
                omitted_count += 1
                continue

            # --- Mapeo de Nombres (Jurados y Tesistas) ---
            def get_user_name_from_docente(id_jurado_antiguo, role):
                if not id_jurado_antiguo: return 'N/A'
                new_docente_id = docentes_map.get(id_jurado_antiguo)
                if not new_docente_id:
                    print(f"    [ADVERTENCIA] Trámite ID {id_tramite_antiguo}: No se encontró nuevo ID de docente para el antiguo ID {id_jurado_antiguo} ({role}).")
                    return 'N/A'
                user_name = usuarios_map.get(new_docente_id, 'N/A')
                if user_name == 'N/A':
                    print(f"    [ADVERTENCIA] Trámite ID {id_tramite_antiguo}: No se encontró nombre de usuario para el nuevo docente ID {new_docente_id} ({role}).")
                return user_name

            presidente = get_user_name_from_docente(tramite_info.get('IdJurado1'), 'Presidente')
            primer_miembro = get_user_name_from_docente(tramite_info.get('IdJurado2'), '1er Miembro')
            segundo_miembro = get_user_name_from_docente(tramite_info.get('IdJurado3'), '2do Miembro')
            asesor = get_user_name_from_docente(tramite_info.get('IdJurado4'), 'Asesor')

            def get_user_name_from_tesista(id_tesista_antiguo, role):
                if not id_tesista_antiguo: return None # Usar None para tesista2 opcional
                id_usuario_nuevo = tesistas_map.get(id_tesista_antiguo)
                if not id_usuario_nuevo:
                    print(f"    [ADVERTENCIA] Trámite ID {id_tramite_antiguo}: No se encontró nuevo ID de usuario para el tesista antiguo ID {id_tesista_antiguo} ({role}).")
                    return 'N/A'
                return usuarios_map.get(id_usuario_nuevo, 'N/A')

            tesista1 = get_user_name_from_tesista(tramite_info.get('IdTesista1'), 'Tesista 1')
            tesista2 = get_user_name_from_tesista(tramite_info.get('IdTesista2'), 'Tesista 2')

            escuela_profesional = carreras_map.get(tramite_info.get('IdCarrera'), 'N/A')

            # --- Lógica de Aprobación ---
            vb_sum = (det.get('vb1') or 0) + (det.get('vb2') or 0) + (det.get('vb3') or 0)
            if vb_sum == 3:
                tipo_aprobacion_id = 27 # APROBADO POR UNANIMIDAD
            elif vb_sum == 2:
                tipo_aprobacion_id = 26 # APROBADO POR MAYORIA
            else:
                tipo_aprobacion_id = 28 # APROBADO POR REGLAMENTO

            # --- Construcción del registro para inserción ---
            record = (
                new_tramite_id,
                tramite_info.get('Codigo'),
                tipo_aprobacion_id,
                det.get('Titulo'),
                tesista1,
                tesista2,
                escuela_profesional,
                presidente,
                primer_miembro,
                segundo_miembro,
                asesor,
                None, # coasesor
                det.get('Fecha'), # fecha_dictamen
                None, # token
                1, # estado
                1, # tipo_acta
                None # folio
            )
            records_to_insert.append(record)

            if idx < 3: # Imprime los primeros 3 registros como muestra
                print(f"  [MUESTRA] Registro a insertar: {record}")


        print(f"\n  Resumen del procesamiento: {total_source} registros leídos, {len(records_to_insert)} preparados para inserción, {omitted_count} omitidos.")

        # 4. Insertar los datos en PostgreSQL
        if records_to_insert:
            print("  Paso 4: Insertando datos en tbl_dictamenes_info...")
            
            insert_query = """
                INSERT INTO tbl_dictamenes_info (
                    id_tramite, codigo_proyecto, tipo_aprobacion, titulo, tesista1, tesista2,
                    escuela_profesional, presidente, primer_miembro, segundo_miembro, asesor,
                    coasesor, fecha_dictamen, token, estado, tipo_acta, folio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            pg_cur.executemany(insert_query, records_to_insert)
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {pg_cur.rowcount} registros.")

        print("--- Migración de tbl_dictamenes_info completada con éxito. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de tbl_dictamenes_info: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_dictamenes_info()
