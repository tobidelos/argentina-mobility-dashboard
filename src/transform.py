import pandas as pd
from typing import Dict, Any, Optional
from src.logger import get_logger

logger = get_logger(__name__)

class DataTransformer:
    """
    A class responsible for cleaning, transforming and merging the extracted data.
    """
    
    def __init__(self):
        pass
        
    def clean_transport_data(self, df: pd.DataFrame, provincia_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Cleans and filters the transport DataFrame. Handle nulls and bad data formatting.
        """
        logger.info("Starting transport data cleaning...")
        # 1. Copia para evitar warnings de Pandas
        df_clean = df.copy()
        
        # Estandarizar nombres de columnas a minúsculas primero para facilitar el acceso
        df_clean.columns = [col.lower() for col in df_clean.columns]
        
        # Limpieza profunda de Nulos y Datos faltantes solicitada por el usuario
        # Si la provincia o municipio es nulo, lo catalogamos como 'Desconocido'
        if 'provincia' in df_clean.columns:
            df_clean['provincia'] = df_clean['provincia'].fillna('Desconocida').astype(str).str.strip().str.title()
        if 'municipio' in df_clean.columns:
            df_clean['municipio'] = df_clean['municipio'].fillna('Desconocido').astype(str).str.strip().str.title()
        if 'jurisdiccion' in df_clean.columns:
            df_clean['jurisdiccion'] = df_clean['jurisdiccion'].fillna('Desconocida').astype(str).str.strip().str.capitalize()
            
        # 2. Filtrar por provincia si se especifica (ahora es None por defecto para traer TODAS)
        if provincia_filter and 'provincia' in df_clean.columns:
            initial_rows = len(df_clean)
            df_clean = df_clean[df_clean['provincia'].str.upper() == provincia_filter.upper()]
            logger.info(f"Filtered by PROVINCIA == '{provincia_filter}'. Rows dropped: {initial_rows - len(df_clean)}")

        # 3. Eliminar columnas irrelevantes
        columns_to_drop = ['dato_preliminar']
        df_clean = df_clean.drop(columns=[col for col in columns_to_drop if col in df_clean.columns])
        
        # 5. Convertir la fecha a datetime (usamos dayfirst=True por el formato DD/MM/YYYY)
        if 'dia_transporte' in df_clean.columns:
            df_clean['dia_transporte'] = pd.to_datetime(df_clean['dia_transporte'], dayfirst=True, errors='coerce')
        
        # 6. Manejo de nulos en cantidad
        if 'cantidad' in df_clean.columns:
            df_clean['cantidad'] = df_clean['cantidad'].fillna(0).astype(int)
            
        # 7. Eliminar filas con fechas nulas (si hubo error al parsear)
        df_clean = df_clean.dropna(subset=['dia_transporte'])
        
        logger.info(f"Transport data cleaned successfully. Final shape: {df_clean.shape}")
        return df_clean

    def clean_weather_data(self, weather_json: Dict[str, Any]) -> pd.DataFrame:
        """
        Transforms the raw Open-Meteo JSON into a daily aggregated pandas DataFrame.
        """
        logger.info("Starting weather data cleaning and aggregation...")
        try:
            # Extraer la llave 'hourly' que contiene las listas de datos
            hourly_data = weather_json.get('hourly')
            if not hourly_data:
                 logger.error("No 'hourly' data found in JSON.")
                 return pd.DataFrame()
                 
            # Crear DataFrame
            df = pd.DataFrame(hourly_data)
            
            # Convertir la columna 'time' a datetime
            df['time'] = pd.to_datetime(df['time'])
            
            # Extraer solo la fecha (ignorando la hora) para poder agrupar por día
            df['date'] = df['time'].dt.normalize()
            
            # Agrupar por día y calcular métricas de negocio
            daily_df = df.groupby('date').agg(
                temp_promedio=('temperature_2m', 'mean'),
                temp_max=('temperature_2m', 'max'),
                temp_min=('temperature_2m', 'min'),
                precipitacion_total=('precipitation', 'sum')
            ).reset_index()
            
            # Redondear temperaturas a 1 decimal
            daily_df['temp_promedio'] = daily_df['temp_promedio'].round(1)
            daily_df['temp_max'] = daily_df['temp_max'].round(1)
            daily_df['temp_min'] = daily_df['temp_min'].round(1)
            
            # Renombrar 'date' a 'dia_transporte' para facilitar el join
            daily_df = daily_df.rename(columns={'date': 'dia_transporte'})
            
            logger.info(f"Weather data aggregated successfully. Shape: {daily_df.shape}")
            return daily_df
        except Exception as e:
            logger.error(f"Error processing weather data: {e}")
            return pd.DataFrame()

    def merge_datasets(self, transport_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merges transport data and weather data on the 'dia_transporte' column.
        """
        logger.info("Merging transport and weather datasets...")
        if transport_df.empty or weather_df.empty:
            logger.warning("One of the datasets is empty. Merge aborted.")
            return pd.DataFrame()
            
        # Left Join: Mantenemos todos los registros de transporte y le agregamos el clima
        merged_df = pd.merge(transport_df, weather_df, on='dia_transporte', how='left')
        
        logger.info(f"Datasets merged successfully. Final shape: {merged_df.shape}")
        return merged_df

if __name__ == "__main__":
    # Test local de transformación
    from src.extract import DataExtractor
    
    # 1. Extracción
    extractor = DataExtractor()
    print("--- 1. Extrayendo datos para prueba ---")
    df_raw_transporte = extractor.extract_transport_data("dat-ab-usos-2025.csv")
    weather_json = extractor.extract_weather_data(
        lat=-34.6037, 
        lon=-58.3816, 
        start_date="2025-01-01", 
        end_date="2025-01-07"
    )
    
    # 2. Transformación
    if df_raw_transporte is not None and weather_json is not None:
        transformer = DataTransformer()
        print("\n--- 2. Transformando datos de Transporte ---")
        df_transporte_clean = transformer.clean_transport_data(df_raw_transporte, provincia_filter="BUENOS AIRES")
        
        print("\n--- 3. Transformando datos del Clima ---")
        df_clima_clean = transformer.clean_weather_data(weather_json)
        
        print("\n--- 4. Realizando Merge ---")
        df_final = transformer.merge_datasets(df_transporte_clean, df_clima_clean)
        
        print("\n--- Muestra del Dataset Final ---")
        print(df_final.head())
        print("\nColumnas finales:", df_final.columns.tolist())
