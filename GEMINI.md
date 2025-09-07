# Resumen del Proyecto

Este proyecto tiene como objetivo migrar dos bases de datos MySQL (`vriunap_absmain` y `vriunap_pilar3`) a una única base de datos PostgreSQL. La migración se realizará en dos fases: primero a una instancia local de PostgreSQL y posteriormente a una base de datos en Supabase.

## Componentes Clave

*   **`db_connections.py`**: Script de Python que gestiona las conexiones a las bases de datos. Contiene la configuración para conectarse a las dos bases de datos de origen en MySQL y a la base de datos de destino en PostgreSQL. La URL de la base de datos de destino se carga desde el archivo `.env`.
*   **`schema_dump.sql`**: Archivo con el volcado del esquema de la base de datos de destino en PostgreSQL. Define la estructura de las tablas que se crearán.
*   **`diccionarios/`**: Directorio que contiene archivos CSV. Estos archivos parecen corresponder a las tablas de diccionario (`dic_`) en el esquema de destino y probablemente se usarán para poblar esas tablas.
*   **`.env`**: Archivo de configuración para almacenar variables de entorno, como la `DATABASE_URL` para la conexión a la base de datos PostgreSQL.

# Ejecución del Proyecto

El script principal para ejecutar la migración, `diccionarios/run_migrate.py`, está actualmente vacío. Es necesario implementar la lógica de migración en este archivo.

**TODO: Implementar la lógica de migración en `diccionarios/run_migrate.py`.**

El flujo de ejecución típico sería:

1.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: El archivo `requirements.txt` no existe. Será necesario crearlo y añadir los paquetes de Python necesarios, como `psycopg2-binary`, `mysql-connector-python` y `python-dotenv`)*

2.  **Configurar el Entorno:**
    *   Crear un archivo `.env` en el directorio raíz.
    *   Añadir la variable `DATABASE_URL` para la base de datos PostgreSQL.
        *   **Para la base de datos local:**
            ```
            DATABASE_URL="postgresql://postgres:admin@localhost:5432/migracion"
            ```
        *   **Para la base de datos de Supabase (ejemplo):**
            ```
            DATABASE_URL="postgres://postgres.abcdefghigklmnopqrst:password@aws-0-us-west-1.pooler.supabase.com:5432/postgres"
            ```

3.  **Ejecutar la Migración:**
    Una vez implementado el script de migración, se ejecutaría desde el directorio raíz de la siguiente manera:
    ```bash
    python diccionarios/run_migrate.py
    ```

# Convenciones de Desarrollo

*   **Conexiones de Base de Datos:** La lógica para las conexiones a las bases de datos está centralizada en `db_connections.py`. Se deben utilizar las funciones de este archivo para establecer las conexiones.
*   **Configuración:** Las configuraciones específicas del entorno, como las URLs de las bases de datos, deben almacenarse en el archivo `.env`.
*   **Diccionarios de Datos:** El directorio `diccionarios/` es la ubicación para los archivos CSV que se utilizan como diccionarios de datos para la migración.

# Análisis de Lógica de Mapeo: Especialidades y Denominaciones

Este análisis es crucial para el remapeo de datos al migrar las tablas transaccionales (`tbl_*`).

### 1. Especialidades (`dic_especialidades`)

Esta es una migración relativamente directa, pero con una **desnormalización importante**.

| `dicEspecialis` (MySQL) | `dic_especialidades` (PostgreSQL) | Lógica de Mapeo |
| :--- | :--- | :--- |
| `Id` | `id` | Mapeo 1 a 1. El ID de la especialidad se conserva. |
| `IdCarrera` | `id_carrera` | Mapeo 1 a 1. La relación con la carrera se conserva. |
| `Nombre` | `nombre` | Mapeo 1 a 1. El nombre de la especialidad se conserva. |
| `Denominacion` | *(Eliminado)* | **Este es el cambio clave.** Este campo ha sido extraído a su propia tabla (`dic_denominaciones`). |
| `Cod` | *(Eliminado)* | Este campo se ha descartado en el nuevo esquema. |

**Lógica de Remapeo para `dic_especialidades`:**
*   La tabla `dic_especialidades` en PostgreSQL es una versión "limpia" de `dicEspecialis` de MySQL.
*   Cuando se migren tablas transaccionales (como `tbl_docentes`) que hagan referencia a un `Id` de `dicEspecialis`, ese `Id` **corresponderá directamente** al `id` en la nueva tabla `dic_especialidades`. **El remapeo aquí es directo.**

---

### 2. Denominaciones (`dic_denominaciones`)

Aquí es donde ocurre la **normalización** de la base de datos. La nueva estructura es más robusta.

**Origen de los Datos:**
No existe una tabla `dicDenominaciones` en MySQL. La información estaba mezclada en la columna `Denominacion` dentro de la tabla `dicEspecialis`. El archivo `dic_denominaciones_rows.csv` fue creado a partir de esa columna para separar y estructurar la información.

**Lógica de la Nueva Estructura:**
*   El nuevo esquema reconoce que una **Especialidad** (ej. "Biología: Ecología") puede otorgar un **Título o Denominación** específico (ej. "Licenciado en Biología: Ecología").
*   La tabla `dic_denominaciones` almacena estos títulos de forma separada y los vincula a la especialidad correspondiente a través de `id_especialidad`.

**Lógica de Remapeo para `dic_denominaciones`:**
*   Este es el remapeo complejo. Cuando se encuentre una tabla en el sistema antiguo que se refiera a un título o denominación, **no se podrá usar un ID para buscarlo**.
*   Se deberá buscar por el **nombre del título** en la nueva tabla `dic_denominaciones` para encontrar el `id` correcto que se necesita para la nueva base de datos.
*   Por ejemplo, si un trámite antiguo dice que el título solicitado es "LICENCIADO EN BIOLOGÍA: ECOLOGÍA", el script de migración deberá:
    1.  Buscar esa cadena de texto en `dic_denominaciones.nombre`.
    2.  Obtener el `id` de esa fila.
    3.  Usar ese `id` para poblar la tabla de trámites en PostgreSQL.

En resumen: **`dic_especialidades` es un remapeo directo de IDs, mientras que `dic_denominaciones` requerirá una búsqueda por nombre para encontrar el nuevo ID.**
