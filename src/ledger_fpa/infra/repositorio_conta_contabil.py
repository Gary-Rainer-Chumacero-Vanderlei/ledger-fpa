from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger_fpa.domain.conta_contabil import ContaContabil, TipoConta
from ledger_fpa.infra.tabelas import ContaContabilTabela, EmpresaTabela


class EmpresaInexistente(Exception):
    """A empresa informada não existe."""


class CodigoContaJaCadastrado(Exception):
    """Já existe uma conta com o código informado na empresa."""


class ContaPaiInexistente(Exception):
    """A conta pai informada não existe na empresa."""


class PaiNaoSintetico(Exception):
    """A conta pai informada não é sintética e não pode ter contas filhas."""


class RepositorioContaContabil:
    """Grava e busca contas de uma empresa, traduzindo domínio e tabela.

    O repositório só enxerga as contas da empresa informada. O código do pai
    (texto, no domínio) é convertido em `conta_pai_id` (inteiro, no banco).
    """

    def __init__(self, sessao: Session, empresa_id: int) -> None:
        self._sessao = sessao
        self._empresa_id = empresa_id

    def adicionar(self, conta: ContaContabil) -> int:
        """Grava a conta e devolve o id gerado pelo banco.

        As regras são verificadas antes de gravar, sem descartar a sessão.
        """
        if self._sessao.get(EmpresaTabela, self._empresa_id) is None:
            raise EmpresaInexistente(self._empresa_id)

        if self._buscar_tabela(conta.codigo) is not None:
            raise CodigoContaJaCadastrado(conta.codigo)

        conta_pai_id = None
        if conta.codigo_pai is not None:
            pai = self._buscar_tabela(conta.codigo_pai)
            if pai is None:
                raise ContaPaiInexistente(conta.codigo_pai)
            if pai.tipo is not TipoConta.SINTETICA:
                raise PaiNaoSintetico(conta.codigo_pai)
            conta_pai_id = pai.id

        tabela = ContaContabilTabela(
            empresa_id=self._empresa_id,
            conta_pai_id=conta_pai_id,
            codigo=conta.codigo,
            nome=conta.nome,
            natureza=conta.natureza,
            tipo=conta.tipo,
        )
        self._sessao.add(tabela)
        self._sessao.flush()

        return tabela.id

    def buscar_por_codigo(self, codigo: str) -> ContaContabil | None:
        tabela = self._buscar_tabela(codigo)
        if tabela is None:
            return None

        codigo_pai = None
        if tabela.conta_pai_id is not None:
            pai = self._sessao.get(ContaContabilTabela, tabela.conta_pai_id)
            codigo_pai = pai.codigo if pai else None

        return _para_dominio(tabela, codigo_pai)

    def listar(self) -> list[ContaContabil]:
        """Lista as contas da empresa em ordem numérica de código."""
        consulta = select(ContaContabilTabela).where(
            ContaContabilTabela.empresa_id == self._empresa_id
        )
        tabelas = list(self._sessao.scalars(consulta))
        codigos = {tabela.id: tabela.codigo for tabela in tabelas}

        contas = [
            _para_dominio(
                tabela,
                codigos.get(tabela.conta_pai_id)
                if tabela.conta_pai_id is not None
                else None,
            )
            for tabela in tabelas
        ]
        return sorted(contas, key=lambda conta: _ordem_do_codigo(conta.codigo))

    def _buscar_tabela(self, codigo: str) -> ContaContabilTabela | None:
        consulta = select(ContaContabilTabela).where(
            ContaContabilTabela.empresa_id == self._empresa_id,
            ContaContabilTabela.codigo == codigo,
        )
        return self._sessao.scalars(consulta).first()


def _para_dominio(tabela: ContaContabilTabela, codigo_pai: str | None) -> ContaContabil:
    return ContaContabil(
        codigo=tabela.codigo,
        nome=tabela.nome,
        natureza=tabela.natureza,
        tipo=tabela.tipo,
        codigo_pai=codigo_pai,
    )


def _ordem_do_codigo(codigo: str) -> tuple[int, ...]:
    return tuple(int(grupo) for grupo in codigo.split("."))
