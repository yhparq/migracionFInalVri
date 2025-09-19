import os
import sys
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=dotenv_path)

# Añadir el directorio raíz del proyecto a sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from db_connections import get_postgres_connection

def subir_archivos_a_supabase():
    """
    Script 2/2: Sube archivos locales a Supabase Storage por lotes,
    con contador de progreso y capacidad de reanudación.
    """
    postgres_conn = get_postgres_connection()
    
    # --- Configuración de Supabase ---
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    bucket_name = "tramites-documentos"
    batch_size = 3000

    if not all([postgres_conn, url, key]):
        print("Error: Falta conexión a PostgreSQL o credenciales de Supabase en .env.")
        return

    try:
        print("--- Iniciando Subida de Archivos a Supabase Storage (por Lotes) ---")

        with postgres_conn.cursor() as cursor:
            # 1. Obtener el conteo total de archivos pendientes
            cursor.execute("SELECT COUNT(*) FROM tbl_archivos_tramites WHERE storage = 'local'")
            total_archivos = cursor.fetchone()[0]
            print(f"  Se encontraron {total_archivos} archivos pendientes para subir.")

            if total_archivos == 0:
                print("  No hay archivos nuevos que subir. Proceso finalizado.")
                return

            # 2. Bucle de procesamiento por lotes
            processed_count = 0
            uploaded_count = 0
            error_count = 0
            
            while True:
                print(f"\n  Obteniendo siguiente lote de hasta {batch_size} archivos...")
                query = f"""
                    SELECT id, id_tramite, nombre_archivo, bucket AS local_path
                    FROM tbl_archivos_tramites
                    WHERE storage = 'local'
                    LIMIT {batch_size}
                """
                df_batch = pd.read_sql(query, postgres_conn)

                if df_batch.empty:
                    print("  No hay más lotes que procesar.")
                    break
                
                print(f"  Procesando {len(df_batch)} archivos en este lote...")
                
                for _, row in df_batch.iterrows():
                    processed_count += 1
                    id_archivo = row['id']
                    id_tramite = row['id_tramite']
                    nombre_archivo = row['nombre_archivo']
                    local_folder_path = row['local_path']
                    
                    local_file_path = os.path.join(local_folder_path, nombre_archivo)
                    supabase_path = f"tramite-{id_tramite}/{nombre_archivo}"

                    # Imprimir progreso en la misma línea
                    progress = f"  Procesando {processed_count}/{total_archivos} ({processed_count/total_archivos:.2%}) - Subiendo: {nombre_archivo}"
                    sys.stdout.write('\r' + progress.ljust(120))
                    sys.stdout.flush()

                    if not os.path.exists(local_file_path):
                        print(f"\n    ADVERTENCIA: Archivo no encontrado en '{local_file_path}'. Saltando.")
                        error_count += 1
                        continue

                    try:
                        # Subir el archivo
                        with open(local_file_path, 'rb') as f:
                            supabase.storage.from_(bucket_name).upload(file=f, path=supabase_path, file_options={"upsert": "true"})
                        
                        # Actualizar el registro en la base de datos
                        update_query = """
                            UPDATE tbl_archivos_tramites
                            SET storage = 'supabase', bucket = %s
                            WHERE id = %s;
                        """
                        cursor.execute(update_query, (bucket_name, id_archivo))
                        uploaded_count += 1

                    except Exception as e:
                        print(f"\n    ERROR al procesar '{nombre_archivo}': {e}")
                        error_count += 1
                        postgres_conn.rollback() # Revertir la transacción del archivo fallido
                        continue
                
                # Confirmar (commit) la transacción para el lote procesado
                postgres_conn.commit()
                print(f"\n  Lote procesado. {uploaded_count} archivos subidos hasta ahora.")

        print("\n\n--- Proceso de Subida de Archivos Completado ---")
        print(f"  Resumen final:")
        print(f"    - Archivos subidos exitosamente: {uploaded_count}")
        print(f"    - Errores o archivos no encontrados: {error_count}")

    except Exception as error:
        print(f"\nError crítico durante el proceso de subida: {error}")
        if postgres_conn: postgres_conn.rollback()
    finally:
        if postgres_conn: postgres_conn.close()
        print("--- Conexión a PostgreSQL cerrada. ---")

if __name__ == "__main__":
    subir_archivos_a_supabase()