import re

_FORMATO = re.compile(r"[0-9A-Z]{12}[0-9]{2}")
_PESOS_PRIMEIRO = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
_PESOS_SEGUNDO = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)


def _digito(caracteres: str, pesos: tuple[int, ...]) -> int:
    soma = sum(
        (ord(caractere) - 48) * peso
        for caractere, peso in zip(caracteres, pesos, strict=True)
    )
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


def cnpj_valido(cnpj: str) -> bool:
    """Indica se o CNPJ, já normalizado, tem dígitos verificadores corretos.

    Espera 14 caracteres em maiúsculas, sem pontuação: 12 numéricos ou
    alfanuméricos e 2 dígitos. Aplica o módulo 11, com cada caractere valendo
    o código ASCII menos 48 (formato alfanumérico da Receita Federal).
    """
    if not _FORMATO.fullmatch(cnpj):
        return False

    if len(set(cnpj)) == 1:
        return False

    primeiro = _digito(cnpj[:12], _PESOS_PRIMEIRO)
    segundo = _digito(cnpj[:13], _PESOS_SEGUNDO)

    return cnpj[12:] == f"{primeiro}{segundo}"
