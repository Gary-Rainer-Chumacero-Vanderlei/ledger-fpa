import re
from dataclasses import dataclass
from enum import Enum

_CODIGO_VALIDO = re.compile(r"\d+(\.\d+)*")


class Natureza(Enum):
    """Lado em que o saldo da conta normalmente aparece."""

    DEVEDORA = "devedora"
    CREDORA = "credora"


class TipoConta(Enum):
    """Sintética agrupa outras contas; analítica recebe lançamentos."""

    SINTETICA = "sintetica"
    ANALITICA = "analitica"


@dataclass(frozen=True)
class ContaContabil:
    """Conta do plano de contas.

    O código é formado por grupos numéricos separados por ponto, como
    1.1.01.001. Apenas contas analíticas aceitam lançamentos.
    """

    codigo: str
    nome: str
    natureza: Natureza
    tipo: TipoConta
    codigo_pai: str | None = None

    def __post_init__(self) -> None:
        nome = self.nome.strip()
        if not nome:
            raise ValueError("O nome da conta não pode ser vazio.")

        if not _CODIGO_VALIDO.fullmatch(self.codigo):
            raise ValueError("O código deve ter grupos numéricos separados por ponto.")

        object.__setattr__(self, "nome", nome)

    @property
    def aceita_lancamento(self) -> bool:
        """Indica se a conta pode receber lançamentos (somente analíticas)."""
        return self.tipo is TipoConta.ANALITICA
