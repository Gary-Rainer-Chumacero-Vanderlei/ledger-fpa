import pytest
from sqlalchemy.orm import Session

from ledger_fpa.domain.conta_contabil import ContaContabil, Natureza, TipoConta
from ledger_fpa.domain.empresa import Empresa
from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.repositorio_conta_contabil import (
    CodigoContaJaCadastrado,
    ContaPaiInexistente,
    EmpresaInexistente,
    PaiNaoSintetico,
    RepositorioContaContabil,
)
from ledger_fpa.infra.repositorio_empresa import RepositorioEmpresa
from ledger_fpa.infra.tabelas import Base


@pytest.fixture
def sessao():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as sessao:
        yield sessao


def _nova_empresa(sessao, cnpj="12345678000195"):
    empresa = Empresa(razao_social="Exemplo Ltda", cnpj=cnpj)
    return RepositorioEmpresa(sessao).adicionar(empresa)


def _conta(**campos):
    dados = {
        "codigo": "1.1.01.001",
        "nome": "Caixa Geral",
        "natureza": Natureza.DEVEDORA,
        "tipo": TipoConta.ANALITICA,
    }
    dados.update(campos)
    return ContaContabil(**dados)


def test_adicionar_devolve_o_id_gerado(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))

    conta_id = repositorio.adicionar(_conta())

    assert isinstance(conta_id, int)


def test_busca_conta_por_codigo(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(_conta())

    conta = repositorio.buscar_por_codigo("1.1.01.001")

    assert conta == _conta()


def test_busca_por_codigo_inexistente_devolve_none(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))

    assert repositorio.buscar_por_codigo("9.9") is None


def test_conta_filha_volta_com_o_codigo_do_pai(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(
        _conta(codigo="1.1.01", nome="Caixa", tipo=TipoConta.SINTETICA)
    )
    repositorio.adicionar(_conta(codigo_pai="1.1.01"))

    conta = repositorio.buscar_por_codigo("1.1.01.001")

    assert conta is not None
    assert conta.codigo_pai == "1.1.01"


def test_rejeita_codigo_duplicado_na_mesma_empresa(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(_conta())

    with pytest.raises(CodigoContaJaCadastrado):
        repositorio.adicionar(_conta(nome="Outro Caixa"))


def test_erro_nao_descarta_o_trabalho_anterior(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(_conta())

    with pytest.raises(CodigoContaJaCadastrado):
        repositorio.adicionar(_conta(nome="Outro Caixa"))

    assert repositorio.buscar_por_codigo("1.1.01.001") is not None
    assert isinstance(repositorio.adicionar(_conta(codigo="1.1.01.002")), int)


def test_rejeita_conta_pai_inexistente(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))

    with pytest.raises(ContaPaiInexistente):
        repositorio.adicionar(_conta(codigo_pai="1.1.01"))


def test_rejeita_conta_pai_de_outra_empresa(sessao):
    repositorio_a = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio_b = RepositorioContaContabil(
        sessao, _nova_empresa(sessao, cnpj="98765432000198")
    )
    repositorio_a.adicionar(
        _conta(codigo="1.1.01", nome="Caixa", tipo=TipoConta.SINTETICA)
    )

    with pytest.raises(ContaPaiInexistente):
        repositorio_b.adicionar(_conta(codigo_pai="1.1.01"))


def test_rejeita_empresa_inexistente(sessao):
    repositorio = RepositorioContaContabil(sessao, 999)

    with pytest.raises(EmpresaInexistente):
        repositorio.adicionar(_conta())


def test_aceita_mesmo_codigo_em_empresas_diferentes(sessao):
    repositorio_a = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio_b = RepositorioContaContabil(
        sessao, _nova_empresa(sessao, cnpj="98765432000198")
    )
    repositorio_a.adicionar(_conta())

    conta_id = repositorio_b.adicionar(_conta())

    assert isinstance(conta_id, int)


def test_busca_nao_enxerga_contas_de_outra_empresa(sessao):
    repositorio_a = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio_b = RepositorioContaContabil(
        sessao, _nova_empresa(sessao, cnpj="98765432000198")
    )
    repositorio_a.adicionar(_conta())

    assert repositorio_b.buscar_por_codigo("1.1.01.001") is None


def test_lista_contas_em_ordem_numerica_de_codigo(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(_conta(codigo="1.10", nome="Dez"))
    repositorio.adicionar(_conta(codigo="1", nome="Ativo"))
    repositorio.adicionar(_conta(codigo="1.2", nome="Dois"))

    codigos = [conta.codigo for conta in repositorio.listar()]

    assert codigos == ["1", "1.2", "1.10"]


def test_lista_traz_o_codigo_do_pai(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(_conta(codigo="1", nome="Ativo", tipo=TipoConta.SINTETICA))
    repositorio.adicionar(_conta(codigo="1.1", nome="Caixa", codigo_pai="1"))

    pais = [conta.codigo_pai for conta in repositorio.listar()]

    assert pais == [None, "1"]


def test_lista_somente_contas_da_empresa(sessao):
    repositorio_a = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio_b = RepositorioContaContabil(
        sessao, _nova_empresa(sessao, cnpj="98765432000198")
    )
    repositorio_a.adicionar(_conta(codigo="1", nome="Ativo"))
    repositorio_b.adicionar(_conta(codigo="2", nome="Passivo"))

    codigos = [conta.codigo for conta in repositorio_b.listar()]

    assert codigos == ["2"]


def test_lista_vazia_quando_nao_ha_contas(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))

    assert repositorio.listar() == []


def test_rejeita_conta_pai_analitica(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(_conta(codigo="1.1.01", nome="Caixa"))

    with pytest.raises(PaiNaoSintetico):
        repositorio.adicionar(_conta(codigo_pai="1.1.01"))


def test_conta_nao_e_gravada_quando_o_pai_e_analitico(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(_conta(codigo="1.1.01", nome="Caixa"))

    with pytest.raises(PaiNaoSintetico):
        repositorio.adicionar(_conta(codigo_pai="1.1.01"))

    assert repositorio.buscar_por_codigo("1.1.01.001") is None


def test_busca_conta_por_id(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    conta_id = repositorio.adicionar(_conta())

    assert repositorio.buscar_por_id(conta_id) == _conta()


def test_busca_por_id_inexistente_devolve_none(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))

    assert repositorio.buscar_por_id(999) is None


def test_busca_por_id_devolve_o_codigo_do_pai(sessao):
    repositorio = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio.adicionar(
        _conta(codigo="1.1.01", nome="Caixa", tipo=TipoConta.SINTETICA)
    )
    conta_id = repositorio.adicionar(_conta(codigo_pai="1.1.01"))

    conta = repositorio.buscar_por_id(conta_id)

    assert conta is not None
    assert conta.codigo_pai == "1.1.01"


def test_busca_por_id_nao_enxerga_conta_de_outra_empresa(sessao):
    repositorio_a = RepositorioContaContabil(sessao, _nova_empresa(sessao))
    repositorio_b = RepositorioContaContabil(
        sessao, _nova_empresa(sessao, cnpj="98765432000198")
    )
    conta_id = repositorio_a.adicionar(_conta())

    assert repositorio_b.buscar_por_id(conta_id) is None
