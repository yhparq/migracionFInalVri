import psycopg2
import mysql.connector
import sys
import os
import io
import csv

# Ajuste del sys.path para permitir importaciones desde el directorio raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_mysql_absmain_connection, get_postgres_connection

def migrate_docente_categoria_historial_mapeado():
    """
    Migra el historial de categorías de docentes desde MySQL a PostgreSQL
    utilizando el comando COPY para una carga masiva de alto rendimiento.
    """
    postgres_conn = None
    mysql_conn = None
    
    print("--- Iniciando migración de historial de categorías de docentes (Modo Rápido) ---")
    
    try:
        # 1. Establecer conexiones a las bases de datos
        postgres_conn = get_postgres_connection()
        mysql_conn = get_mysql_absmain_connection()

        if not all([postgres_conn, mysql_conn]):
            raise Exception("No se pudieron establecer todas las conexiones necesarias.")

        pg_cursor = postgres_conn.cursor()
        mysql_cursor = mysql_conn.cursor(dictionary=True)

        # 2. Crear un mapa de IDs: id_antiguo (MySQL) -> nuevo id (PostgreSQL)
        print("Paso 1: Creando mapa de IDs de docentes desde PostgreSQL...")
        pg_cursor.execute("SELECT id, id_antiguo FROM public.tbl_docentes WHERE id_antiguo IS NOT NULL")
        
        docente_id_map = {row[1]: row[0] for row in pg_cursor.fetchall()}
        
        if not docente_id_map:
            print("Advertencia: No se encontraron docentes con 'id_antiguo' en PostgreSQL. No se puede continuar.")
            return
            
        print(f"Se mapearon {len(docente_id_map)} docentes.")

        # 3. Leer todos los registros de la tabla de docentes original en MySQL
        print("\nPaso 2: Leyendo todos los docentes desde MySQL...")
        mysql_cursor.execute("SELECT Id, IdCategoria, FechaAsc, ResolAsc FROM tblDocentes")
        all_mysql_docentes = mysql_cursor.fetchall()
        print(f"Se encontraron {len(all_mysql_docentes)} registros en la tabla de origen.")

        # 4. Preparar los datos para la carga masiva
        print("\nPaso 3: Mapeando y preparando los registros para la carga masiva...")
        historial_to_insert = []
        
        for docente in all_mysql_docentes:
            old_docente_id = docente.get('Id')
            new_docente_id = docente_id_map.get(old_docente_id)
            
            if new_docente_id:
                # Asegurarse de que los valores nulos de MySQL se manejen como None
                fecha_asc = docente.get('FechaAsc')
                resol_asc = docente.get('ResolAsc')

                mapped_record = (
                    new_docente_id,
                    docente.get('IdCategoria'),
                    fecha_asc,
                    resol_asc,
                    1  # Estado activo por defecto
                )
                historial_to_insert.append(mapped_record)
        
        print(f"Se prepararon {len(historial_to_insert)} registros de historial para insertar.")

        # 5. Usar COPY para una inserción masiva y eficiente
        if historial_to_insert:
            print("\nPaso 4: Limpiando la tabla de destino (tbl_docente_categoria_historial)...")
            pg_cursor.execute("TRUNCATE TABLE public.tbl_docente_categoria_historial RESTART IDENTITY;")
            
            print(f"Paso 5: Insertando {len(historial_to_insert)} registros usando COPY...")
            
            # Crear un buffer en memoria
            buffer = io.StringIO()
            writer = csv.writer(buffer, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(historial_to_insert)
            buffer.seek(0)
            
            # Ejecutar el comando COPY
            cols = ('id_docente', 'id_categoria', 'fecha_resolucion', 'resolucion', 'estado')
            pg_cursor.copy_expert(f"COPY public.tbl_docente_categoria_historial ({', '.join(cols)}) FROM STDIN WITH CSV DELIMITER E'\\t'", buffer)
            
            # Confirmar la transacción
            postgres_conn.commit()
            print("¡Migración del historial de categorías completada con éxito!")
        else:
            print("\nNo se encontraron registros de historial para migrar.")

    except (Exception, psycopg2.Error, mysql.connector.Error) as e:
        print(f"\nERROR: Ocurrió un problema durante la migración: {e}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        # 6. Cerrar conexiones
        print("\nCerrando conexiones a las bases de datos.")
        if postgres_conn:
            postgres_conn.close()
        if mysql_conn:
            mysql_conn.close()

if __name__ == "__main__":
    migrate_docente_categoria_historial_mapeado()
