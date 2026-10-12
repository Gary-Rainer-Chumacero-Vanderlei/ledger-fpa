from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ledger_fpa.domain.empresa import Empresa
from ledger_fpa.infra.tabelas import EmpresaTabela


class CnpjJaCadastrado(Exception):
    """Já existe uma empresa com o CNPJ informado."""


class RepositorioEmpresa:
    """Grava e busca empresas, traduzindo entre o domínio e a tabela."""

    def __init__(self, sessao: Session) -> None:
        self._sessao = sessao

    def adicionar(self, empresa: Empresa) -> int:
        """Grava a empresa e devolve o id gerado pelo banco."""
        tabela = EmpresaTabela(razao_social=empresa.razao_social, cnpj=empresa.cnpj)
        self._sessao.add(tabela)

        try:
            self._sessao.flush()
        except IntegrityError as erro:
            self._sessao.rollback()
            raise CnpjJaCadastrado(empresa.cnpj) from erro

        return tabela.id

    def buscar_por_id(self, empresa_id: int) -> Empresa | None:
        tabela = self._sessao.get(EmpresaTabela, empresa_id)
        return _para_dominio(tabela) if tabela else None

    def buscar_por_cnpj(self, cnpj: str) -> Empresa | None:
        consulta = select(EmpresaTabela).where(EmpresaTabela.cnpj == cnpj)
        tabela = self._sessao.scalars(consulta).first()
        return _para_dominio(tabela) if tabela else None

    def listar(self) -> list[Empresa]:
        consulta = select(EmpresaTabela).order_by(EmpresaTabela.razao_social)
        return [_para_dominio(t) for t in self._sessao.scalars(consulta)]


def _para_dominio(tabela: EmpresaTabela) -> Empresa:
    return Empresa(razao_social=tabela.razao_social, cnpj=tabela.cnpj)
