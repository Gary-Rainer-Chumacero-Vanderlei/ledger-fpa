from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger_fpa.infra.repositorio_conta_contabil import EmpresaInexistente
from ledger_fpa.infra.tabelas import (
    ContaContabilTabela,
    EmpresaTabela,
    LancamentoTabela,
    TransacaoImportadaTabela,
)


class ContaDoBancoInexistente(Exception):
    """A conta contábil do banco não existe na empresa."""


class LancamentoInexistente(Exception):
    """O lançamento informado não existe na empresa."""


class TransacaoJaImportada(Exception):
    """A transação já foi importada para esta conta do banco."""


class RepositorioTransacaoImportada:
    """Registra as transações de extrato que já viraram lançamento.

    É isolado por empresa e pela conta contábil do banco: o mesmo
    identificador (FITID) pode existir em outra conta ou em outra empresa.
    Evita importar a mesma transação duas vezes (ADR 0005).
    """

    def __init__(self, sessao: Session, empresa_id: int, conta_id: int) -> None:
        self._sessao = sessao
        self._empresa_id = empresa_id
        self._conta_id = conta_id

    def ja_importadas(self, identificadores: Iterable[str]) -> set[str]:
        """Devolve, entre os identificadores informados, os já registrados."""
        procurados = set(identificadores)
        if not procurados:
            return set()

        consulta = select(TransacaoImportadaTabela.identificador).where(
            TransacaoImportadaTabela.empresa_id == self._empresa_id,
            TransacaoImportadaTabela.conta_id == self._conta_id,
            TransacaoImportadaTabela.identificador.in_(procurados),
        )
        return set(self._sessao.scalars(consulta))

    def registrar(self, identificador: str, lancamento_id: int) -> None:
        """Registra que a transação virou o lançamento informado."""
        if not identificador.strip():
            raise ValueError("O identificador não pode ser vazio.")

        if self._sessao.get(EmpresaTabela, self._empresa_id) is None:
            raise EmpresaInexistente(self._empresa_id)

        conta = self._sessao.get(ContaContabilTabela, self._conta_id)
        if conta is None or conta.empresa_id != self._empresa_id:
            raise ContaDoBancoInexistente(self._conta_id)

        lancamento = self._sessao.get(LancamentoTabela, lancamento_id)
        if lancamento is None or lancamento.empresa_id != self._empresa_id:
            raise LancamentoInexistente(lancamento_id)

        if identificador in self.ja_importadas([identificador]):
            raise TransacaoJaImportada(identificador)

        self._sessao.add(
            TransacaoImportadaTabela(
                empresa_id=self._empresa_id,
                conta_id=self._conta_id,
                lancamento_id=lancamento_id,
                identificador=identificador,
            )
        )
        self._sessao.flush()
