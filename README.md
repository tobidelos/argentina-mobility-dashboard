# Observatorio Analítico de Movilidad Urbana 🚍🚆⛈️

Este proyecto es una plataforma integral de **Business Intelligence (BI) y Data Engineering** desarrollada para monitorear, analizar y visualizar los flujos de transporte terrestre en Argentina utilizando los datos oficiales del Sistema Único de Boleto Electrónico (SUBE). Además, cruza esta información volumétrica con **datos meteorológicos históricos (API REST)** para medir el impacto de variables climáticas en el comportamiento de los pasajeros.

---

## 🚀 Arquitectura y Tecnologías Utilizadas

El proyecto está diseñado bajo una arquitectura modular separando la capa de ingeniería de datos (ETL) de la capa de visualización interactiva.

### Stack Tecnológico
* **Lenguaje Core:** Python 3.10+
* **Data Engineering (ETL):** `pandas` (limpieza, transformación y cruce de datos masivos)
* **Base de Datos / Data Warehouse:** `SQLite3` (almacenamiento local optimizado y relacional)
* **Consumo de APIs:** `requests` (integración con la API REST de Open-Meteo para datos climáticos)
* **Frontend / Visualización:** `Streamlit` (framework web) y `Plotly` (gráficos dinámicos e interactivos)
* **Deployment:** `Docker` (contenerización lista para la nube)

---

## ⚙️ Pipeline de Datos (ETL)

El corazón de este proyecto es su motor ETL (`main.py`) que orquesta tres clases fundamentales:

1. **`DataExtractor` (Extract):** 
   - Realiza la ingesta masiva de más de **540,000 registros** provenientes de un archivo CSV gubernamental. 
   - Resuelve asincrónicamente el consumo de la API de *Open-Meteo* para descargar el clima histórico diario de todo el año (temperaturas máximas, precipitaciones).
2. **`DataTransformer` (Transform):** 
   - **Limpieza de datos:** Resuelve errores nativos del dataset del gobierno (conflictos de *encoding*, caracteres rotos, jurisdicciones faltantes y mapeos de nombres).
   - **Geocodificación y Mapeo:** Utiliza expresiones regulares (`regex`) para reasignar dinámicamente datos incompletos del Subte y AMBA hacia sus jurisdicciones geográficas y administrativas correspondientes.
   - **Merge relacional:** Cruza la matriz de transporte con la serie de tiempo meteorológica (`LEFT JOIN`).
3. **`DataLoader` (Load):** 
   - Carga el DataFrame final limpio y cruzado en un motor relacional `SQLite`, preparándolo para consumo rápido y cacheable por la herramienta analítica.

---

## 📊 Dashboard Interactivo (BI)

El archivo `dashboard.py` levanta una interfaz analítica en Streamlit diseñada con foco en UX corporativo y escalabilidad:

* **Métricas Clave (KPIs):** Algoritmos que calculan la resiliencia climática del transporte (impacto porcentual de las lluvias y temperaturas mayores a 30°C vs días templados/secos) y el desplome de uso durante fines de semana.
* **Filtros Dinámicos Cascadados:** Segmentación de datos a nivel Nacional, Provincial y Jurisdiccional (Nacional/Provincial/Municipal), re-calculando toda la UI en tiempo real.
* **Series de Tiempo y Mapas de Calor:** Análisis temporales aplicando medias móviles (rolling averages) para suavizar anomalías, y *heatmaps* para descubrir patrones de concentración semanal.

---

## 🛠️ Instrucciones de Ejecución Local

Para levantar el proyecto en un entorno local paso a paso:

1. **Clonar el repositorio y crear el entorno virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux/Mac
   venv\Scripts\activate     # En Windows
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el motor ETL (Solo la primera vez):**
   *Asegúrate de tener el archivo oficial de transporte (CSV) en la raíz.*
   ```bash
   python main.py
   ```
   *Esto generará la base de datos `movilidad_urbana.db` cruzando el CSV con la API climática.*

4. **Lanzar el Dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

---

## 🐳 Despliegue con Docker

El proyecto se encuentra totalmente contenerizado para garantizar su funcionamiento en cualquier servidor o plataforma Cloud (AWS, Azure, GCP).

**Construir la imagen:**
```bash
docker build -t observatorio-transporte .
```

**Levantar el contenedor:**
```bash
docker run -p 8501:8501 observatorio-transporte
```
*El dashboard estará accesible en http://localhost:8501*

---
*Desarrollado con foco en limpieza de datos, rendimiento de bases relacionales y visualización de alto impacto corporativo.*
