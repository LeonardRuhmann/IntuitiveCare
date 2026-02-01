import pytest
import pandas as pd
import os
import sys
import zipfile

# Path Setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.zip_processor import ZipProcessor

@pytest.fixture
def mock_zip_path(tmp_path):
    """
    Creates a temporary ZIP file containing a valid CSV (UTF-8) for testing.
    """
    csv_content = """DATA;REG_ANS;CD_CONTA_CONTABIL;DESCRICAO;VL_SALDO_FINAL
2025-01-01;123456;1111;Despesas com Eventos/Sinistros;100,50
2025-01-01;123456;2222;Outra Despesa;200,00"""
    
    zip_file = tmp_path / "test_file.zip"
    csv_name = "test_data.csv"
    
    #  Create the ZIP file
    with zipfile.ZipFile(zip_file, 'w') as zf:
        zf.writestr(csv_name, csv_content.encode('utf-8'))
        
    return str(zip_file)

def test_process_zip_success(mock_zip_path):
    """Test if we can extract and read a standard CSV from a ZIP."""
    processor = ZipProcessor()
    
    df = processor.process_zip(mock_zip_path)
    
    # Verification
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1  # We put 2 rows in the CSV
    
    # Check for the column (handling potential renaming)
    assert 'ValorDespesas' in df.columns or 'VL_SALDO_FINAL' in df.columns
    
    # Check value accuracy
    # If the column was renamed to ValorDespesas, check that
    col_name = 'ValorDespesas' if 'ValorDespesas' in df.columns else 'VL_SALDO_FINAL'
    assert df.iloc[0][col_name] == 100.50

def test_process_invalid_zip(tmp_path):
    """Test how the code handles a non-zip file."""
    # Create a fake file that is NOT a zip
    bad_file = tmp_path / "bad.zip"
    bad_file.write_text("This is not a zip file", encoding='utf-8')
    
    processor = ZipProcessor()
    
    # Expectation: It should return None (graceful failure)
    result = processor.process_zip(str(bad_file))
    assert result is None