from decimal import Decimal

_CENTAVO = Decimal("0.01")


def para_centavos(valor: Decimal) -> int:
    """Converte um valor em reais (Decimal) para centavos (int).

    Aceita no máximo duas casas decimais. É a fronteira entre o domínio,
    que usa Decimal, e o banco, que guarda inteiros (ADR 0002).
    """
    if not isinstance(valor, Decimal):
        raise TypeError("O valor deve ser um Decimal.")

    if not valor.is_finite() or valor != valor.quantize(_CENTAVO):
        raise ValueError("O valor deve ser finito e ter no máximo duas casas.")

    return int(valor.scaleb(2))


def de_centavos(centavos: int) -> Decimal:
    """Converte centavos (int) para reais (Decimal com duas casas)."""
    if not isinstance(centavos, int) or isinstance(centavos, bool):
        raise TypeError("Os centavos devem ser um inteiro.")

    return Decimal(centavos).scaleb(-2)
