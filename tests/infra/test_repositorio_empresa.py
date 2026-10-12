import pytest
from sqlalchemy.orm import Session

from ledger_fpa.domain.empresa import Empresa
from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.repositorio_empresa import (
    CnpjJaCadastrado,
    RepositorioEmpresa,
)
from ledger_fpa.infra.tabelas import Base


@pytest.fixture
def sessao():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as sessao:
        yield sessao


def _empresa(**campos):
    dados = {"razao_social": "Exemplo Ltda", "cnpj": "12.345.678/0001-95"}
    dados.update(campos)
    return Empresa(**dados)


def test_adicionar_devolve_o_id_gerado(sessao):
    repositorio = RepositorioEmpresa(sessao)

    empresa_id = repositorio.adicionar(_empresa())

    assert isinstance(empresa_id, int)


def test_busca_empresa_por_id(sessao):
    repositorio = RepositorioEmpresa(sessao)
    empresa_id = repositorio.adicionar(_empresa())

    empresa = repositorio.buscar_por_id(empresa_id)

    assert empresa == _empresa()


def test_busca_empresa_por_cnpj(sessao):
    repositorio = RepositorioEmpresa(sessao)
    repositorio.adicionar(_empresa())

    empresa = repositorio.buscar_por_cnpj("12345678000195")

    assert empresa == _empresa()


def test_busca_por_id_inexistente_devolve_none(sessao):
    repositorio = RepositorioEmpresa(sessao)

    assert repositorio.buscar_por_id(999) is None


def test_busca_por_cnpj_inexistente_devolve_none(sessao):
    repositorio = RepositorioEmpresa(sessao)

    assert repositorio.buscar_por_cnpj("00000000000000") is None


def test_rejeita_cnpj_duplicado(sessao):
    repositorio = RepositorioEmpresa(sessao)
    repositorio.adicionar(_empresa())

    with pytest.raises(CnpjJaCadastrado):
        repositorio.adicionar(_empresa(razao_social="Outra Ltda"))


def test_repositorio_continua_utilizavel_apos_cnpj_duplicado(sessao):
    repositorio = RepositorioEmpresa(sessao)
    repositorio.adicionar(_empresa())

    with pytest.raises(CnpjJaCadastrado):
        repositorio.adicionar(_empresa(razao_social="Outra Ltda"))

    empresa_id = repositorio.adicionar(_empresa(cnpj="98.765.432/0001-98"))

    assert isinstance(empresa_id, int)


def test_lista_empresas_ordenadas_por_razao_social(sessao):
    repositorio = RepositorioEmpresa(sessao)
    repositorio.adicionar(_empresa(razao_social="Zeta Ltda", cnpj="11111111000191"))
    repositorio.adicionar(_empresa(razao_social="Alfa Ltda", cnpj="22222222000191"))

    empresas = repositorio.listar()

    assert [e.razao_social for e in empresas] == ["Alfa Ltda", "Zeta Ltda"]


def test_lista_vazia_quando_nao_ha_empresas(sessao):
    repositorio = RepositorioEmpresa(sessao)

    assert repositorio.listar() == []


def test_erro_de_cnpj_duplicado_nao_descarta_o_trabalho_anterior(sessao):
    repositorio = RepositorioEmpresa(sessao)
    repositorio.adicionar(_empresa(cnpj="11111111000191"))
    repositorio.adicionar(_empresa(cnpj="22222222000191"))

    with pytest.raises(CnpjJaCadastrado):
        repositorio.adicionar(_empresa(cnpj="22222222000191"))

    assert repositorio.buscar_por_cnpj("11111111000191") is not None
    assert repositorio.buscar_por_cnpj("22222222000191") is not None
