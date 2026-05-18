# Dashboard ADN Electoral

Aplicación Streamlit para explorar el índice **ADN Electoral de Mesa** a partir de datos electorales consolidados.

## Disclaimer legal

Esta herramienta es una visualización analítica independiente y no oficial. Las tipologías, índices y agrupaciones ideológicas son criterios de análisis propios y no forman parte de los resultados oficiales.

Los datos oficiales pueden consultarse y descargarse en:

https://resultados.eleccionesparlamentoandalucia2026.es/es/descargas

## Qué muestra

- Tipología de mesas: isla, inversora, frontera, amplificador, líquida, ancla y mixta.
- Filtros por provincia, municipio, tipo ADN y partido.
- Número de mesas y votos contemplados por cada selección.
- Comparativa de bloques derecha/izquierda en las mesas filtradas.
- Tabla de mesas destacadas y gráfico conceptual de rareza ADN frente a brecha de bloques.
- Descarga en CSV de las mesas filtradas y del resumen por tipo.
- Explicaciones integradas de rareza ADN, margen del ganador, fragmentación y brecha de bloques.

## Datos

Los datos se incluyen en:

`data/mesas_adn_electoral.parquet`

El Parquet está comprimido y contiene solo las columnas necesarias para la app.

## Despliegue en Streamlit Cloud

1. Sube esta carpeta a un repositorio de GitHub.
2. En Streamlit Cloud, crea una nueva app.
3. Selecciona como archivo principal:

`app.py`

4. Streamlit instalará las dependencias desde:

`requirements.txt`

## Seguridad

- La app no permite subir archivos.
- No ejecuta código proporcionado por usuarios.
- Lee únicamente un Parquet local incluido en el repositorio.
- Los filtros de texto se aplican como búsqueda literal, sin expresiones regulares.
- No requiere secretos, claves de API ni conexiones externas.

## Ejecución local

```bash
pip install -r requirements.txt
streamlit run app.py
```
