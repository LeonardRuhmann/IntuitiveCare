import re

def validate_cnpj(cnpj: str) -> bool:
    """
    Validates a CNPJ using the standard check digit algorithm.
    Expects a string.
    """
    if not cnpj:
        return False

    #  Remove non-digits
    cnpj = re.sub(r'[^0-9]', '', str(cnpj))

    # If it's a valid but stripped CNPJ, this makes it 14 digits again
    if 10 <= len(cnpj) < 14:
        cnpj = cnpj.zfill(14)
    
    #  Check length and repetitive digits (ex: 00000000000000, 11111111111111, etc..)
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False

    #  Algorithm to verify check digits (Verificador Standard)
    def calculate_digit(cnpj_body, weights):
        soma = sum(int(digit) * weight for digit, weight in zip(cnpj_body, weights))
        remainder = soma % 11
        return 0 if remainder < 2 else 11 - remainder

    # First Digit
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digit_1 = calculate_digit(cnpj[:12], weights_1)

    # Second Digit
    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    digit_2 = calculate_digit(cnpj[:13], weights_2)

    return cnpj[-2:] == f"{digit_1}{digit_2}"