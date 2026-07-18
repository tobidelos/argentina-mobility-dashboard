import pandas as pd
from src.transform import DataTransformer

def test_clean_transport_data():
    """
    Prueba que los nulos se reemplacen correctamente durante la limpieza.
    """
    # Arrange
    raw_data = {
        'PROVINCIA': [None, 'C.a.b.a', 'Córdoba'],
        'MUNICIPIO': [None, 'Comuna 1', 'Capital'],
        'JURISDICCION': [None, 'Municipal', 'Provincial'],
        'CANTIDAD': [None, 100, 50],
        'DIA_TRANSPORTE': ['01/01/2025', '02/01/2025', '03/01/2025'],
        'TIPO_TRANSPORTE': ['Colectivo', 'Subte', 'Tren'],
        'LINEA': ['123', 'A', 'Mitre'],
        'NOMBRE_EMPRESA': ['Empresa 1', 'Empresa 2', 'Empresa 3'],
        'DATO_PRELIMINAR': ['Si', 'No', 'Si']
    }
    df_raw = pd.DataFrame(raw_data)
    transformer = DataTransformer()
    
    # Act
    df_clean = transformer.clean_transport_data(df_raw, provincia_filter=None)
    
    # Assert
    assert 'dato_preliminar' not in df_clean.columns
    assert df_clean.iloc[0]['provincia'] == 'Desconocida'
    assert df_clean.iloc[0]['municipio'] == 'Desconocido'
    assert df_clean.iloc[0]['jurisdiccion'] == 'Desconocida'
    assert df_clean.iloc[0]['cantidad'] == 0
    assert len(df_clean) == 3
