import pandas as pd
import sqlite3
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLoader:
    """
    A class responsible for loading transformed data into the target data warehouse (SQLite).
    """
    
    def __init__(self, db_path: str = "data_warehouse.db"):
        """
        Initializes the DataLoader.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path

    def load_to_sqlite(self, df: pd.DataFrame, table_name: str = "fact_usos_vs_clima", if_exists: str = "replace") -> bool:
        """
        Loads the DataFrame into a SQLite database table.

        Args:
            df (pd.DataFrame): The DataFrame to load.
            table_name (str): The name of the table in the database.
            if_exists (str): What to do if the table exists ('fail', 'replace', 'append').

        Returns:
            bool: True if successful, False otherwise.
        """
        if df is None or df.empty:
            logger.error("The DataFrame is empty or None. Aborting load.")
            return False

        logger.info(f"Connecting to SQLite database at {self.db_path}...")
        try:
            # Context manager asegura que la conexión se cierre correctamente incluso si hay error
            with sqlite3.connect(self.db_path) as conn:
                logger.info(f"Loading {len(df)} rows into table '{table_name}'...")
                
                # Pandas to_sql se encarga de crear la tabla y mapear los tipos de datos de Pandas a SQL
                df.to_sql(name=table_name, con=conn, if_exists=if_exists, index=False)
                
                logger.info("Data loaded successfully into SQLite.")
                return True
                
        except sqlite3.Error as sql_e:
            logger.error(f"SQLite database error occurred: {sql_e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during loading: {e}")
            return False

if __name__ == "__main__":
    # Test local simplificado
    pass
