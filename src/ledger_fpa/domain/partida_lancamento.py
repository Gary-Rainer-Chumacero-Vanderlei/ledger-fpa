from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from ledger_fpa.domain.conta_contabil import ContaContabil

_CENTAVO = Decimal("0.01")


class TipoPartida(Enum):
    """Lado da partida: débito ou crédito."""

    DEBITO = "D"
    CREDITO = "C"


@dataclass(frozen=True)
class PartidaLancamento:
    """Uma linha de um lançamento: conta, lado (débito ou crédito) e valor.

    O valor deve ser um Decimal positivo com no máximo duas casas decimais,
    e a conta deve aceitar lançamentos (analítica).
    """

    conta: ContaContabil
    tipo: TipoPartida
    valor: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            raise TypeError("O valor deve ser um Decimal.")

        if not self.valor.is_finite() or self.valor <= 0:
            raise ValueError("O valor deve ser positivo.")

        if self.valor != self.valor.quantize(_CENTAVO):
            raise ValueError("O valor deve ter no máximo duas casas decimais.")

        if not self.conta.aceita_lancamento:
            raise ValueError("A conta deve ser analítica para receber lançamentos.")
