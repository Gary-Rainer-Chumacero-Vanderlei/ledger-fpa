from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger_fpa.domain.conta_contabil import TipoConta
from ledger_fpa.domain.lancamento import Lancamento
from ledger_fpa.domain.partida_lancamento import PartidaLancamento
from ledger_fpa.infra.dinheiro import de_centavos, para_centavos
from ledger_fpa.infra.repositorio_conta_contabil import (
    EmpresaInexistente,
    RepositorioContaContabil,
)
from ledger_fpa.infra.tabelas import (
    ContaContabilTabela,
    EmpresaTabela,
    LancamentoTabela,
    PartidaLancamentoTabela,
)


class LoteJaCadastrado(Exception):
    """Já existe um lançamento com o lote informado na empresa."""


class ContaInexistente(Exception):
    """A conta de uma partida não existe na empresa."""


class ContaNaoAnalitica(Exception):
    """A conta de uma partida não é analítica e não recebe lançamentos."""


class RepositorioLancamento:
    """Grava e busca lançamentos de uma empresa, com suas partidas.

    O lançamento ocupa duas tabelas. Todas as regras são verificadas antes de
    gravar qualquer linha, para que ele seja gravado por inteiro ou não seja.
    """

    def __init__(self, sessao: Session, empresa_id: int) -> None:
        self._sessao = sessao
        self._empresa_id = empresa_id
        self._contas = RepositorioContaContabil(sessao, empresa_id)

    def adicionar(self, lancamento: Lancamento) -> int:
        """Grava o lançamento e as partidas, e devolve o id do lançamento."""
        if self._sessao.get(EmpresaTabela, self._empresa_id) is None:
            raise EmpresaInexistente(self._empresa_id)

        if self._buscar_tabela(lancamento.lote) is not None:
            raise LoteJaCadastrado(lancamento.lote)

        contas = [self._conta_da_partida(p) for p in lancamento.partidas]

        cabecalho = LancamentoTabela(
            empresa_id=self._empresa_id,
            data=lancamento.data,
            lote=lancamento.lote,
            historico=lancamento.historico,
        )
        self._sessao.add(cabecalho)
        self._sessao.flush()

        for partida, conta in zip(lancamento.partidas, contas, strict=True):
            self._sessao.add(
                PartidaLancamentoTabela(
                    lancamento_id=cabecalho.id,
                    conta_id=conta.id,
                    tipo=partida.tipo,
                    valor_centavos=para_centavos(partida.valor),
                )
            )
        self._sessao.flush()

        return cabecalho.id

    def buscar_por_lote(self, lote: int) -> Lancamento | None:
        cabecalho = self._buscar_tabela(lote)
        return self._montar(cabecalho) if cabecalho else None

    def listar(self) -> list[Lancamento]:
        """Lista os lançamentos da empresa, por data e lote."""
        consulta = (
            select(LancamentoTabela)
            .where(LancamentoTabela.empresa_id == self._empresa_id)
            .order_by(LancamentoTabela.data, LancamentoTabela.lote)
        )
        cabecalhos = self._sessao.scalars(consulta).all()
        return [self._montar(cabecalho) for cabecalho in cabecalhos]

    def _conta_da_partida(self, partida: PartidaLancamento) -> ContaContabilTabela:
        codigo = partida.conta.codigo
        consulta = select(ContaContabilTabela).where(
            ContaContabilTabela.empresa_id == self._empresa_id,
            ContaContabilTabela.codigo == codigo,
        )
        conta = self._sessao.scalars(consulta).first()

        if conta is None:
            raise ContaInexistente(codigo)

        if conta.tipo is not TipoConta.ANALITICA:
            raise ContaNaoAnalitica(codigo)

        return conta

    def _buscar_tabela(self, lote: int) -> LancamentoTabela | None:
        consulta = select(LancamentoTabela).where(
            LancamentoTabela.empresa_id == self._empresa_id,
            LancamentoTabela.lote == lote,
        )
        return self._sessao.scalars(consulta).first()

    def _montar(self, cabecalho: LancamentoTabela) -> Lancamento:
        consulta = (
            select(PartidaLancamentoTabela)
            .where(PartidaLancamentoTabela.lancamento_id == cabecalho.id)
            .order_by(PartidaLancamentoTabela.id)
        )
        partidas = tuple(self._partida(t) for t in self._sessao.scalars(consulta))

        return Lancamento(
            data=cabecalho.data,
            lote=cabecalho.lote,
            historico=cabecalho.historico,
            partidas=partidas,
        )

    def _partida(self, tabela: PartidaLancamentoTabela) -> PartidaLancamento:
        conta = self._contas.buscar_por_id(tabela.conta_id)
        if conta is None:
            raise RuntimeError(f"Conta {tabela.conta_id} da partida não encontrada.")

        return PartidaLancamento(
            conta=conta,
            tipo=tabela.tipo,
            valor=de_centavos(tabela.valor_centavos),
        )
