import pandas as pd
import requests
import os
from src.logger import get_logger
from typing import Dict, Any, Optional

logger = get_logger(__name__)

class DataExtractor:
    """
    Class responsible for extracting data from various sources (CSV, APIs).
    """

    def __init__(self):
        """
        Initializes the DataExtractor.
        """
        pass

    def extract_transport_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Extracts public transport data from a local CSV file.

        Args:
            file_path (str): The absolute or relative path to the CSV file.

        Returns:
            Optional[pd.DataFrame]: A pandas DataFrame containing the extracted data, 
                                    or None if extraction fails.
        """
        try:
            logger.info(f"Attempting to load transport data from: {file_path}")
            # Intentamos primero con utf-8, que es el estándar, y especificamos el separador ';'
            df = pd.read_csv(file_path, encoding='utf-8', sep=';')
            logger.info(f"Successfully loaded transport data. Shape: {df.shape}")
            return df
        
        except FileNotFoundError:
            logger.error(f"Error: The file {file_path} was not found.")
            return None
        except UnicodeDecodeError:
            logger.warning("UTF-8 decoding failed. Attempting with latin1 encoding...")
            try:
                # Si falla utf-8, intentamos con latin1, común en archivos generados en Windows en LATAM
                df = pd.read_csv(file_path, encoding='latin1', sep=';')
                logger.info(f"Successfully loaded transport data with latin1 encoding. Shape: {df.shape}")
                return df
            except Exception as e:
                logger.error(f"Error decoding file {file_path} with latin1: {e}")
                return None
        except pd.errors.EmptyDataError:
            logger.error(f"Error: The file {file_path} is empty.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while reading the CSV: {e}")
            return None

    def extract_weather_data(self, lat: float, lon: float, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
        """
        Extracts historical weather data from the Open-Meteo API (Free & No API Key required).

        Args:
            lat (float): Latitude of the location.
            lon (float): Longitude of the location.
            start_date (str): Start date in YYYY-MM-DD format.
            end_date (str): End date in YYYY-MM-DD format.

        Returns:
            Optional[Dict[str, Any]]: A JSON dictionary containing the weather data, 
                                      or None if extraction fails.
        """
        url = "https://archive-api.open-meteo.com/v1/archive"
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'start_date': start_date,
            'end_date': end_date,
            'hourly': 'temperature_2m,precipitation', # Variables clave de impacto
            'timezone': 'America/Argentina/Buenos_Aires' # Ajuste al uso horario local
        }

        try:
            logger.info(f"Requesting weather data for coords ({lat}, {lon}) from {start_date} to {end_date}")
            # Definimos un timeout para evitar que el proceso se quede colgado
            response = requests.get(url, params=params, timeout=10)
            
            # Lanza una excepción si el status code HTTP es 4xx o 5xx
            response.raise_for_status() 
            
            logger.info("Successfully fetched weather data.")
            return response.json()
        
        except requests.exceptions.Timeout:
            logger.error("Error: The request to the Open-Meteo API timed out.")
            return None
        except requests.exceptions.HTTPError as err:
            logger.error(f"HTTP error occurred: {err}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Error: Could not connect to the Open-Meteo API. Check your internet connection.")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"An unexpected error occurred during the API request: {e}")
            return None

if __name__ == "__main__":
    # Este bloque es solo para pruebas locales (se ejecuta si corres el archivo directamente)
    
    # Instanciamos la clase (ya no requiere API Key para Open-Meteo)
    extractor = DataExtractor()
    
    # Prueba 1: Extraer CSV
    print("--- Probando Extracción CSV ---")
    transport_df = extractor.extract_transport_data("dat-ab-usos-2025.csv")
    if transport_df is not None:
        print(transport_df.head())
    
    # Prueba 2: Extraer API (Coordenadas de Buenos Aires como ejemplo, primeros 7 días del 2025)
    print("\n--- Probando Extracción API (Open-Meteo) ---")
    weather_data = extractor.extract_weather_data(
        lat=-34.6037, 
        lon=-58.3816, 
        start_date="2025-01-01", 
        end_date="2025-01-07"
    )
    if weather_data:
        print("Datos del clima obtenidos exitosamente. Llaves principales devueltas:")
        print(weather_data.keys())

