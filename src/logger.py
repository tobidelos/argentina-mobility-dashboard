import logging
import sys

def get_logger(name: str = "ETL_Orchestrator") -> logging.Logger:
    """
    Retorna un logger configurado de forma estandarizada para todo el proyecto.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
    return logger
