from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

_CENTAVO = Decimal("0.01")


class Sentido(Enum):
    """Efeito da transação no saldo do banco: entrada (soma) ou saída (subtrai)."""

    SOMA = "soma"
    SUBTRAI = "subtrai"


@dataclass(frozen=True)
class TransacaoExtrato:
    """Uma transação lida de um extrato bancário.

    A data é a que o banco escreveu, sem hora nem fuso. O valor é sempre
    positivo (Decimal, até duas casas): quem diz se entra ou sai do banco é o
    sentido. O identificador (FITID) é único na conta e evita importar a mesma
    transação duas vezes. O documento é opcional.
    """

    data: date
    historico: str
    valor: Decimal
    sentido: Sentido
    identificador: str
    documento: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.data, date) or isinstance(self.data, datetime):
            raise TypeError("A data deve ser um date, sem hora.")

        historico = self.historico.strip()
        if not historico:
            raise ValueError("O histórico não pode ser vazio.")

        identificador = self.identificador.strip()
        if not identificador:
            raise ValueError("O identificador não pode ser vazio.")

        if not isinstance(self.valor, Decimal):
            raise TypeError("O valor deve ser um Decimal.")

        if not self.valor.is_finite() or self.valor <= 0:
            raise ValueError("O valor deve ser positivo.")

        if self.valor != self.valor.quantize(_CENTAVO):
            raise ValueError("O valor deve ter no máximo duas casas decimais.")

        documento = (self.documento or "").strip() or None

        object.__setattr__(self, "historico", historico)
        object.__setattr__(self, "identificador", identificador)
        object.__setattr__(self, "documento", documento)
