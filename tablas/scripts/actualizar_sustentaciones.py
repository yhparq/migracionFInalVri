
import psycopg2
import sys
import os

# Add parent directory to allow module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

def actualizar_sustentaciones_y_coasesor():
    """
    Actualiza tbl_dictamenes_info con la fecha y lugar de sustentación desde tesSustens
    y el nombre del co-asesor desde tesTramites (IdJurado5).
    """
    print("--- Iniciando actualización de datos de sustentación y co-asesor ---")
    pg_conn = None
    mysql_conn_pilar3 = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn_pilar3 = get_mysql_pilar3_connection()

        if not all([pg_conn, mysql_conn_pilar3]):
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur_pilar3 = mysql_conn_pilar3.cursor(dictionary=True)

        print("  Paso 1: Creando mapas de traducción...")
        
        # Mapa de trámites: id_antiguo (MySQL) -> id_nuevo (PostgreSQL)
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        tramites_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        # Mapa de docentes: id_antiguo (MySQL) -> id_usuario_nuevo (PostgreSQL)
        pg_cur.execute("SELECT id_antiguo, id_usuario FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docentes_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        # Mapa de usuarios: id_usuario_nuevo (PostgreSQL) -> nombre_completo
        pg_cur.execute("SELECT id, CONCAT(nombres, ' ', apellidos) as full_name FROM tbl_usuarios")
        usuarios_map = {row[0]: row[1] for row in pg_cur.fetchall()}

        print("  Paso 2: Obteniendo datos de co-asesor (IdJurado5) desde tesTramites...")
        mysql_cur_pilar3.execute("SELECT Id, IdJurado5 FROM tesTramites WHERE IdJurado5 IS NOT NULL AND IdJurado5 != 0")
        coasesor_map = {row['Id']: row['IdJurado5'] for row in mysql_cur_pilar3.fetchall()}

        print("  Paso 3: Obteniendo datos de sustentación desde tesSustens...")
        mysql_cur_pilar3.execute("SELECT IdTramite, Fecha, Lugar FROM tesSustens")
        sustentaciones = mysql_cur_pilar3.fetchall()
        total_sustentaciones = len(sustentaciones)
        print(f"  Se encontraron {total_sustentaciones} registros de sustentación para procesar.")

        print("  Paso 4: Procesando y preparando actualizaciones...")
        updates_to_execute = []
        omitted_count = 0
        
        for sustentacion in sustentaciones:
            id_tramite_antiguo = sustentacion['IdTramite']
            
            # Buscar el nuevo ID del trámite
            id_tramite_nuevo = tramites_map.get(id_tramite_antiguo)
            if not id_tramite_nuevo:
                omitted_count += 1
                continue

            # Obtener datos de la sustentación
            fecha_sustentacion = sustentacion.get('Fecha')
            lugar_sustentacion = sustentacion.get('Lugar')

            # Obtener y mapear el nombre del co-asesor
            nombre_coasesor = None
            id_coasesor_antiguo = coasesor_map.get(id_tramite_antiguo)
            if id_coasesor_antiguo:
                id_usuario_coasesor = docentes_map.get(id_coasesor_antiguo)
                if id_usuario_coasesor:
                    nombre_coasesor = usuarios_map.get(id_usuario_coasesor, 'Co-asesor no encontrado')

            # Añadir a la lista de actualizaciones
            updates_to_execute.append({
                'id_tramite': id_tramite_nuevo,
                'fecha': fecha_sustentacion,
                'lugar': lugar_sustentacion,
                'coasesor': nombre_coasesor
            })

        print(f"\n  Resumen: {len(updates_to_execute)} actualizaciones preparadas, {omitted_count} registros omitidos.")

        if updates_to_execute:
            print("  Paso 5: Ejecutando actualizaciones en tbl_dictamenes_info...")
            
            # Usar un enfoque más robusto para la actualización
            update_query = """
                UPDATE tbl_dictamenes_info
                SET fecha_sustentacion = %s,
                    lugar_sustentacion = %s,
                    coasesor = %s
                WHERE id_tramite = %s
            """
            
            # Convertir el diccionario a una lista de tuplas para executemany
            update_tuples = [
                (d['fecha'], d['lugar'], d['coasesor'], d['id_tramite'])
                for d in updates_to_execute
            ]

            pg_cur.executemany(update_query, update_tuples)
            pg_conn.commit()
            print(f"  ¡Éxito! Se actualizaron {pg_cur.rowcount} registros en la base de datos.")

        print("\n--- Proceso de actualización de sustentaciones y co-asesor finalizado. ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO durante la actualización: {e}")
        if pg_conn: pg_conn.rollback()
    finally:
        if pg_conn: pg_conn.close()
        if mysql_conn_pilar3: mysql_conn_pilar3.close()
        print("--- Conexiones cerradas. ---")

if __name__ == '__main__':
    actualizar_sustentaciones_y_coasesor()
