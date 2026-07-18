import sys

# Importamos las clases de nuestros módulos modulares
from src.extract import DataExtractor
from src.transform import DataTransformer
from src.load import DataLoader
from src.logger import get_logger
from src.config import TRANSPORT_CSV_PATH, DB_PATH, API_LAT, API_LON, START_DATE, END_DATE

logger = get_logger("ETL_Orchestrator")

def run_etl_pipeline():
    """
    Main function to orchestrate the entire ETL pipeline.
    """
    logger.info("="*50)
    logger.info("Starting Mobility ETL Pipeline")
    logger.info("="*50)
    
    # ---------------------------------------------------------
    # FASE 1: EXTRACT
    # ---------------------------------------------------------
    logger.info("\n--- PHASE 1: EXTRACT ---")
    extractor = DataExtractor()
    
    # 1.1 Extraer CSV Local
    df_raw_transporte = extractor.extract_transport_data(str(TRANSPORT_CSV_PATH))
    if df_raw_transporte is None:
        logger.critical("Transport data extraction failed. Terminating ETL.")
        return
        
    # 1.2 Extraer Clima vía API (Todo el año)
    weather_json = extractor.extract_weather_data(
        lat=API_LAT, 
        lon=API_LON, 
        start_date=START_DATE, 
        end_date=END_DATE
    )
    if not weather_json:
        logger.critical("Weather data extraction failed. Terminating ETL.")
        return

    # ---------------------------------------------------------
    # FASE 2: TRANSFORM
    # ---------------------------------------------------------
    logger.info("\n--- PHASE 2: TRANSFORM ---")
    transformer = DataTransformer()
    
    # 2.1 Limpiar Transporte (Se cargan TODAS las provincias de Argentina)
    df_transporte_clean = transformer.clean_transport_data(df_raw_transporte, provincia_filter=None)
    
    # 2.2 Limpiar y Agregar Clima
    df_clima_clean = transformer.clean_weather_data(weather_json)
    
    # 2.3 Cruzar Datasets
    df_final = transformer.merge_datasets(df_transporte_clean, df_clima_clean)
    
    if df_final.empty:
        logger.critical("Transformation resulted in an empty dataset. Terminating ETL.")
        return

    # ---------------------------------------------------------
    # FASE 3: LOAD
    # ---------------------------------------------------------
    logger.info("\n--- PHASE 3: LOAD ---")
    loader = DataLoader(db_path=str(DB_PATH))
    
    success = loader.load_to_sqlite(df_final, table_name="usos_vs_clima", if_exists="replace")
    
    # ---------------------------------------------------------
    # RESUMEN Y FIN
    # ---------------------------------------------------------
    logger.info("\n" + "="*50)
    if success:
        logger.info(f"ETL Pipeline completed SUCCESSFULLY! Data is ready in '{DB_PATH.name}'")
    else:
        logger.error("ETL Pipeline failed during the Load phase.")
    logger.info("="*50)

if __name__ == "__main__":
    run_etl_pipeline()
