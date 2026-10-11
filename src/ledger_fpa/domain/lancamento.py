from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ledger_fpa.domain.partida_lancamento import PartidaLancamento, TipoPartida


def _soma(partidas: tuple[PartidaLancamento, ...], tipo: TipoPartida) -> Decimal:
    return sum((p.valor for p in partidas if p.tipo is tipo), start=Decimal("0"))


@dataclass(frozen=True)
class Lancamento:
    """Lançamento contábil pelo método das partidas dobradas.

    A soma dos débitos deve ser igual à soma dos créditos. O lote deve ser
    positivo e o histórico não pode ser vazio.
    """

    data: date
    lote: int
    historico: str
    partidas: tuple[PartidaLancamento, ...]

    def __post_init__(self) -> None:
        historico = self.historico.strip()
        if not historico:
            raise ValueError("O histórico não pode ser vazio.")

        if self.lote <= 0:
            raise ValueError("O lote deve ser positivo.")

        partidas = tuple(self.partidas)
        if not partidas:
            raise ValueError("O lançamento deve ter ao menos uma partida.")

        debitos = _soma(partidas, TipoPartida.DEBITO)
        creditos = _soma(partidas, TipoPartida.CREDITO)
        if debitos != creditos:
            raise ValueError("A soma dos débitos deve ser igual à dos créditos.")

        object.__setattr__(self, "historico", historico)
        object.__setattr__(self, "partidas", partidas)
