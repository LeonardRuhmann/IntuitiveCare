import pytest
from src.utils.validators import validate_cnpj

def test_cnpj_valid():
    # A real valid CNPJ (Google Brasil)
    assert validate_cnpj("06.990.590/0001-23") is True
    # Clean version
    assert validate_cnpj("06990590000123") is True

def test_cnpj_invalid_digits():
    # Wrong check digits
    assert validate_cnpj("06.990.590/0001-24") is False

def test_cnpj_invalid_length():
    assert validate_cnpj("123") is False

def test_cnpj_repeated():
    # This is a common fake CNPJ that passes math but is invalid
    assert validate_cnpj("00000000000000") is False

def test_cnpj_empty():
    assert validate_cnpj("") is False
    assert validate_cnpj(None) is False

def test_cnpj_stripped_zeros():
    cnpj_stripped = "6990590000123"
    
    assert validate_cnpj(cnpj_stripped) is True
