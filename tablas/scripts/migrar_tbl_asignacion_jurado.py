import psycopg2
import io
import sys
import os
from db_connections import get_postgres_connection, get_mysql_pilar3_connection

# Ajuste del sys.path para permitir importaciones desde el directorio raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def get_tipo_evento(motivo):
    """Convierte el motivo textual en un ID de tipo de evento."""
    if not motivo:
        return 7 # Default si el motivo es nulo o vacío
    motivo_lower = motivo.lower()
    if 'intento' in motivo_lower: return 1
    if 'sorteo' in motivo_lower: return 4
    return 7 # Default para otros casos

def migrate_tbl_asignacion_jurado_fast():
    """
    Migra el historial de cambios de jurado desde tesJuCambios (MySQL) a 
    tbl_asignacion_jurado (PostgreSQL) utilizando el método COPY para una carga masiva de alto rendimiento.
    """
    print("--- Iniciando migración de tbl_asignacion_jurado (Método COPY) ---")
    pg_conn = None
    mysql_conn = None
    try:
        pg_conn = get_postgres_connection()
        mysql_conn = get_mysql_pilar3_connection()

        if pg_conn is None or mysql_conn is None:
            raise Exception("No se pudo conectar a una de las bases de datos.")

        pg_cur = pg_conn.cursor()
        mysql_cur = mysql_conn.cursor(dictionary=True)

        # 1. Crear mapas de IDs para una rápida traducción
        print("  Paso 1: Creando mapas de IDs desde PostgreSQL...")
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_docentes WHERE id_antiguo IS NOT NULL")
        docente_map = {row[1]: row[0] for row in pg_cur.fetchall()}
        
        pg_cur.execute("SELECT id, id_antiguo FROM tbl_tramites WHERE id_antiguo IS NOT NULL")
        tramites_map = {row[1]: row[0] for row in pg_cur.fetchall()}

        pg_cur.execute("SELECT id FROM tbl_usuarios WHERE correo = 'sistema@vriunap.pe'")
        system_user_row = pg_cur.fetchone()
        if system_user_row is None:
            raise Exception("El usuario 'sistema@vriunap.pe' no fue encontrado en la tabla tbl_usuarios. Por favor, créelo antes de continuar.")
        system_user_id = system_user_row[0]
        
        print(f"  Mapeo completado: {len(docente_map)} docentes, {len(tramites_map)} trámites.")

        # 2. Leer datos de origen, ordenados para la lógica de iteración
        print("  Paso 2: Extrayendo datos de tesJuCambios desde MySQL...")
        mysql_cur.execute("SELECT * FROM tesJuCambios ORDER BY IdTramite, Fecha ASC")
        source_data = mysql_cur.fetchall()
        print(f"  Se extrajeron {len(source_data)} registros de cambios de jurado.")

        # 3. Procesar y preparar datos en memoria
        print("  Paso 3: Procesando y transformando datos...")
        data_for_copy = []
        iteracion_tracker = {}
        unmapped_jurados = 0
        jurado_fields = ['IdJurado1', 'IdJurado2', 'IdJurado3', 'IdJurado4']

        for row in source_data:
            id_tramite_antiguo = row['IdTramite']
            new_tramite_id = tramites_map.get(id_tramite_antiguo)
            if not new_tramite_id:
                continue

            current_iteracion = iteracion_tracker.get(id_tramite_antiguo, 0) + 1
            iteracion_tracker[id_tramite_antiguo] = current_iteracion
            id_tipo_evento = get_tipo_evento(row['Motivo'])

            for i, field in enumerate(jurado_fields):
                old_docente_id = row[field]
                if old_docente_id and old_docente_id > 0:
                    new_docente_id = docente_map.get(old_docente_id)
                    if new_docente_id:
                        # El orden debe coincidir con el COPY
                        data_for_copy.append(
                            (
                                new_tramite_id, 5, i + 1, current_iteracion, id_tipo_evento,
                                new_docente_id, system_user_id, row['Fecha'], 0
                            )
                        )
                    else:
                        unmapped_jurados += 1
        
        print(f"  Se prepararon {len(data_for_copy)} registros para la carga masiva.")
        if unmapped_jurados > 0:
            print(f"  ADVERTENCIA: Se ignoraron {unmapped_jurados} jurados sin mapeo de ID.")

        # 4. Cargar los datos en PostgreSQL usando COPY
        if data_for_copy:
            print("  Paso 4: Cargando datos en PostgreSQL con COPY...")
            
            buffer = io.StringIO()
            for record in data_for_copy:
                # Convertir cada registro a una línea de texto separada por tabuladores
                # Usamos '\N' para representar NULL, que es el estándar para COPY
                line = '\t'.join(str(item) if item is not None else '\\N' for item in record)
                buffer.write(line + '\n')
            
            buffer.seek(0) # Rebobinar el buffer al principio

            # Definir las columnas en el orden correcto
            columns = (
                'tramite_id', 'id_etapa', 'id_orden', 'iteracion', 'id_tipo_evento',
                'docente_id', 'id_usuario_asignador', 'fecha_evento', 'estado'
            )
            
            # Ejecutar el comando COPY, especificando '\N' como el marcador de NULL
            pg_cur.copy_expert(
                sql=f"COPY public.tbl_asignacion_jurado ({', '.join(columns)}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '\\N')",
                file=buffer
            )
            
            pg_conn.commit()
            print(f"  Carga masiva completada. Se insertaron {len(data_for_copy)} registros.")

        print("--- Migración de tbl_asignacion_jurado completada con éxito ---")

    except Exception as e:
        print(f"  ERROR CRÍTICO en migración de asignación de jurados: {e}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if pg_conn:
            pg_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("--- Conexiones cerradas ---")

if __name__ == '__main__':
    migrate_tbl_asignacion_jurado_fast()
