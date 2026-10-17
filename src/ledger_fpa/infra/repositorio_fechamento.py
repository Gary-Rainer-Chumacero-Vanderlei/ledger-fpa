from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger_fpa.domain.competencia import Competencia
from ledger_fpa.infra.repositorio_conta_contabil import EmpresaInexistente
from ledger_fpa.infra.tabelas import EmpresaTabela, FechamentoTabela


class FechamentoForaDeSequencia(Exception):
    """A competência informada não é a seguinte à última fechada."""


class RepositorioFechamento:
    """Guarda e consulta o fechamento de período de uma empresa.

    A empresa tem no máximo um registro, com a última competência fechada.
    O primeiro fechamento pode ser de qualquer competência. Os seguintes só
    aceitam a competência imediatamente posterior à última fechada.
    """

    def __init__(self, sessao: Session, empresa_id: int) -> None:
        self._sessao = sessao
        self._empresa_id = empresa_id

    def ultima_competencia_fechada(self) -> Competencia | None:
        tabela = self._buscar_tabela()
        return _para_dominio(tabela) if tabela else None

    def esta_fechada(self, competencia: Competencia) -> bool:
        """Indica se a competência é igual ou anterior à última fechada."""
        ultima = self.ultima_competencia_fechada()
        return ultima is not None and competencia <= ultima

    def fechar(self, competencia: Competencia) -> None:
        """Fecha a competência, respeitando a sequência dos meses."""
        if self._sessao.get(EmpresaTabela, self._empresa_id) is None:
            raise EmpresaInexistente(self._empresa_id)

        tabela = self._buscar_tabela()

        if tabela is None:
            self._sessao.add(
                FechamentoTabela(
                    empresa_id=self._empresa_id,
                    ano=competencia.ano,
                    mes=competencia.mes,
                )
            )
            self._sessao.flush()
            return

        esperada = _para_dominio(tabela).proxima()
        if competencia != esperada:
            raise FechamentoForaDeSequencia(
                f"Esperada {esperada}, recebida {competencia}."
            )

        tabela.ano = competencia.ano
        tabela.mes = competencia.mes
        self._sessao.flush()

    def _buscar_tabela(self) -> FechamentoTabela | None:
        consulta = select(FechamentoTabela).where(
            FechamentoTabela.empresa_id == self._empresa_id
        )
        return self._sessao.scalars(consulta).first()


def _para_dominio(tabela: FechamentoTabela) -> Competencia:
    return Competencia(ano=tabela.ano, mes=tabela.mes)
