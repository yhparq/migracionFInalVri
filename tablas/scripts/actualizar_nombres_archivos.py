import os
import sys
import re
import psycopg2
from psycopg2.extras import execute_batch

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection

def actualizar_nombres_y_registros():
    """
    Script de corrección:
    1. Lee la tabla tbl_archivos_tramites en PostgreSQL.
    2. Busca archivos cuyo nombre contenga el patrón 'P<numero>-'.
    3. Renombra los archivos físicos en el disco para quitar ese patrón.
    4. Actualiza los registros correspondientes en la base de datos.
    """
    postgres_conn = get_postgres_connection()
    if not postgres_conn:
        print("Error: No se pudo conectar a PostgreSQL.")
        return

    # IMPORTANTE: Asegúrate de que esta ruta sea la correcta.
    source_files_path = "/Users/nachiparra/Documents/tesis/docs"
    
    registros_a_actualizar = []
    
    try:
        print("--- Iniciando corrección de nombres de archivos y registros ---")
        
        with postgres_conn.cursor() as cursor:
            print("  Paso 1: Obteniendo registros de archivos desde PostgreSQL...")
            cursor.execute("SELECT id, nombre_archivo FROM public.tbl_archivos_tramites")
            archivos_en_db = cursor.fetchall()
            print(f"  Se encontraron {len(archivos_en_db)} registros.")

            # --- Fase de Renombrado Físico ---
            print("\n  Paso 2: Renombrando archivos físicos en el disco...")
            renamed_count = 0
            rename_errors = 0
            for archivo_id, nombre_actual in archivos_en_db:
                # Comprueba si el nombre contiene el patrón a eliminar (ej. 'P16-')
                if re.search(r'P\d+-', nombre_actual):
                    nombre_corregido = re.sub(r'P\d+-', '', nombre_actual)
                    
                    ruta_actual = os.path.join(source_files_path, nombre_actual)
                    ruta_corregida = os.path.join(source_files_path, nombre_corregido)
                    
                    if os.path.exists(ruta_actual):
                        try:
                            os.rename(ruta_actual, ruta_corregida)
                            print(f"    - Renombrado: '{nombre_actual}' -> '{nombre_corregido}'")
                            renamed_count += 1
                            # Solo añadimos para actualizar en BD si el renombrado físico fue exitoso
                            registros_a_actualizar.append((nombre_corregido, archivo_id))
                        except OSError as e:
                            print(f"    - ERROR al renombrar '{nombre_actual}': {e}")
                            rename_errors += 1
                    else:
                        # Si el archivo no existe, quizás ya fue renombrado o está perdido.
                        # Lo añadimos para actualizar en la BD de todas formas.
                        registros_a_actualizar.append((nombre_corregido, archivo_id))

            print(f"  Resumen de renombrado: {renamed_count} archivos renombrados, {rename_errors} errores.")

            # --- Fase de Actualización en Base de Datos ---
            if not registros_a_actualizar:
                print("\nNo hay registros en la base de datos que necesiten ser actualizados.")
                return

            print(f"\n  Paso 3: Actualizando {len(registros_a_actualizar)} registros en la base de datos...")
            update_query = "UPDATE public.tbl_archivos_tramites SET nombre_archivo = %s WHERE id = %s"
            
            execute_batch(cursor, update_query, registros_a_actualizar)
            
            postgres_conn.commit()
            print("  ¡Actualización de la base de datos completada con éxito!")

    except (Exception, psycopg2.Error) as error:
        print(f"\nError durante el proceso de corrección: {error}")
        if postgres_conn:
            postgres_conn.rollback()
    finally:
        if postgres_conn:
            postgres_conn.close()
        print("\n--- Proceso de corrección finalizado. ---")

if __name__ == "__main__":
    actualizar_nombres_y_registros()
