import psycopg2
import sys
import os
from db_connections import get_postgres_connection, get_mysql_pilar3_connection, get_mysql_absmain_connection

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def migrate_tbl_dictamenes_info():
    """
    VERSIÓN MEJORADA: Puebla la tabla tbl_dictamenes_info consolidando datos.
    - tipo_aprobacion es un INTEGER mapeado a dic_acciones.
    - Incluye valores por defecto para 'tipo_acta' y 'folio'.
    - Añade logging detallado para identificar registros omitidos o con datos faltantes.
    - Lógica de denominación y escuela profesional corregida.
    """
    print("--- Iniciando migración MEJORADA para poblar tbl_dictamenes_info ---")
    pg_conn = None
    mysql_conn_pilar3 = None
    mysql_conn_absmain = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn_pilar3 = get_mysql_pilar3_connection()
        mysql_conn_absmain = get_mysql_absmain_connection()

        if not all([pg_conn, mysql_conn_pilar3, mysql_conn_absmain]):
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur_pilar3 = mysql_conn_pilar3.cursor(dictionary=True)
        mysql_cur_absmain = mysql_conn_absmain.cursor(dictionary=True)

        print("  Paso 1: Creando mapas de traducción y búsqueda...")
        
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        tramites_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docentes_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id, CONCAT(nombres, ' ', apellidos) as full_name FROM tbl_usuarios")
        usuarios_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id_antiguo, id_usuario FROM tbl_tesistas WHERE id_antiguo IS NOT NULL")
        tesistas_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        mysql_cur_pilar3.execute("SELECT Id, Codigo, IdTesista1, IdTesista2, IdJurado1, IdJurado2, IdJurado3, IdJurado4 FROM tesTramites")
        tes_tramites_map = {row['Id']: row for row in mysql_cur_pilar3.fetchall()}
        
        mysql_cur_pilar3.execute("SELECT Id, IdCarrera, idEspec FROM tblTesistas")
        tesistas_academic_map = {row['Id']: {'IdCarrera': row['IdCarrera'], 'idEspec': row['idEspec']} for row in mysql_cur_pilar3.fetchall()}

        mysql_cur_absmain.execute("SELECT Id, Nombre, Titulo FROM dicCarreras")
        carreras_info_map = {row['Id']: {'Nombre': row['Nombre'], 'Titulo': row['Titulo']} for row in mysql_cur_absmain.fetchall()}

        mysql_cur_absmain.execute("SELECT Id, Denominacion FROM dicEspecialis")
        especialis_denominacion_map = {row['Id']: row['Denominacion'] for row in mysql_cur_absmain.fetchall()}

        print(f"  Mapeos completados.")

        print("  Paso 2: Obteniendo dictámenes de Iteración 3 desde MySQL...")
        mysql_cur_pilar3.execute("SELECT Id, IdTramite, Titulo, vb1, vb2, vb3, Fecha FROM tesTramsDet WHERE Iteracion = 3")
        source_dictamenes = mysql_cur_pilar3.fetchall()
        total_source = len(source_dictamenes)
        print(f"  Se encontraron {total_source} dictámenes para procesar.")

        print("  Paso 3: Procesando y transformando datos...")
        records_to_insert = []
        omitted_count = 0
        
        for idx, det in enumerate(source_dictamenes):
            id_tramite_antiguo = det['IdTramite']
            id_detalle_antiguo = det['Id']

            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            if not new_tramite_id:
                omitted_count += 1
                continue

            tramite_info = tes_tramites_map.get(id_tramite_antiguo)
            if not tramite_info:
                omitted_count += 1
                continue

            def get_user_name_from_docente(id_jurado_antiguo, role):
                if not id_jurado_antiguo: return 'N/A'
                new_docente_id = docentes_map.get(id_jurado_antiguo)
                if not new_docente_id: return 'N/A'
                return usuarios_map.get(new_docente_id, 'N/A')

            presidente = get_user_name_from_docente(tramite_info.get('IdJurado1'), 'Presidente')
            primer_miembro = get_user_name_from_docente(tramite_info.get('IdJurado2'), '1er Miembro')
            segundo_miembro = get_user_name_from_docente(tramite_info.get('IdJurado3'), '2do Miembro')
            asesor = get_user_name_from_docente(tramite_info.get('IdJurado4'), 'Asesor')

            def get_user_name_from_tesista(id_tesista_antiguo, role):
                if not id_tesista_antiguo: return None
                id_usuario_nuevo = tesistas_map.get(id_tesista_antiguo)
                if not id_usuario_nuevo: return 'N/A'
                return usuarios_map.get(id_usuario_nuevo, 'N/A')

            tesista1 = get_user_name_from_tesista(tramite_info.get('IdTesista1'), 'Tesista 1')
            tesista2 = get_user_name_from_tesista(tramite_info.get('IdTesista2'), 'Tesista 2')

            # --- LÓGICA PARA ESCUELA PROFESIONAL Y DENOMINACIÓN ---
            id_tesista1_antiguo = tramite_info.get('IdTesista1')
            tesista_academico_info = tesistas_academic_map.get(id_tesista1_antiguo)
            
            escuela_profesional = "Escuela no encontrada"
            denominacion_final = "Denominación no encontrada"

            if tesista_academico_info:
                id_carrera = tesista_academico_info['IdCarrera']
                id_especialidad = tesista_academico_info['idEspec']
                
                carrera_info = carreras_info_map.get(id_carrera)
                if carrera_info:
                    escuela_profesional = carrera_info.get('Nombre', escuela_profesional)
                
                if id_especialidad == 0:
                    if carrera_info:
                        denominacion_final = carrera_info.get('Titulo', "Título no encontrado")
                else:
                    denominacion_final = especialis_denominacion_map.get(id_especialidad, "Denominación de especialidad no encontrada")
            # --- FIN DE LA LÓGICA ---

            vb_sum = (det.get('vb1') or 0) + (det.get('vb2') or 0) + (det.get('vb3') or 0)
            if vb_sum == 3: tipo_aprobacion_id = 27
            elif vb_sum == 2: tipo_aprobacion_id = 26
            else: tipo_aprobacion_id = 28

            record = (
                new_tramite_id, tramite_info.get('Codigo'), tipo_aprobacion_id,
                det.get('Titulo'), denominacion_final, tesista1, tesista2, escuela_profesional,
                presidente, primer_miembro, segundo_miembro, asesor,
                None, det.get('Fecha'), None, 1, 1, None
            )
            records_to_insert.append(record)

        print(f"\n  Resumen del procesamiento: {total_source} registros leídos, {len(records_to_insert)} preparados para inserción, {omitted_count} omitidos.")

        if records_to_insert:
            print("  Paso 4: Insertando datos en tbl_dictamenes_info...")
            insert_query = """
                INSERT INTO tbl_dictamenes_info (
                    id_tramite, codigo_proyecto, tipo_aprobacion, titulo, denominacion, tesista1, tesista2,
                    escuela_profesional, presidente, primer_miembro, segundo_miembro, asesor,
                    coasesor, fecha_dictamen, token, estado, tipo_acta, folio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            pg_cur.executemany(insert_query, records_to_insert)
            pg_conn.commit()
            print(f"  ¡Éxito! Se insertaron {pg_cur.rowcount} registros.")

        print("--- Migración de tbl_dictamenes_info completada con éxito. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en la migración de tbl_dictamenes_info: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if pg_conn: pg_conn.close()
        if mysql_conn_pilar3: mysql_conn_pilar3.close()
        if mysql_conn_absmain: mysql_conn_absmain.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    migrate_tbl_dictamenes_info()