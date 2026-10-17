import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger_fpa.domain.competencia import Competencia
from ledger_fpa.domain.empresa import Empresa
from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.repositorio_conta_contabil import EmpresaInexistente
from ledger_fpa.infra.repositorio_empresa import RepositorioEmpresa
from ledger_fpa.infra.repositorio_fechamento import (
    FechamentoForaDeSequencia,
    RepositorioFechamento,
)
from ledger_fpa.infra.tabelas import Base, FechamentoTabela


@pytest.fixture
def sessao():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as sessao:
        yield sessao


def _nova_empresa(sessao, cnpj="12345678000195"):
    empresa = Empresa(razao_social="Exemplo Ltda", cnpj=cnpj)
    return RepositorioEmpresa(sessao).adicionar(empresa)


def test_sem_fechamento_nao_ha_ultima_competencia(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))

    assert repositorio.ultima_competencia_fechada() is None


def test_primeiro_fechamento_pode_ser_de_qualquer_competencia(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))

    repositorio.fechar(Competencia(2017, 12))

    assert repositorio.ultima_competencia_fechada() == Competencia(2017, 12)


def test_fecha_a_competencia_seguinte(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio.fechar(Competencia(2017, 12))

    repositorio.fechar(Competencia(2018, 1))

    assert repositorio.ultima_competencia_fechada() == Competencia(2018, 1)


def test_avancar_o_fechamento_atualiza_o_mesmo_registro(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio.fechar(Competencia(2017, 12))
    repositorio.fechar(Competencia(2018, 1))

    registros = sessao.scalars(select(FechamentoTabela)).all()

    assert len(registros) == 1


def test_rejeita_pular_uma_competencia(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio.fechar(Competencia(2017, 12))

    with pytest.raises(FechamentoForaDeSequencia):
        repositorio.fechar(Competencia(2018, 2))


def test_rejeita_fechar_a_mesma_competencia_de_novo(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio.fechar(Competencia(2017, 12))

    with pytest.raises(FechamentoForaDeSequencia):
        repositorio.fechar(Competencia(2017, 12))


def test_rejeita_fechar_competencia_anterior(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio.fechar(Competencia(2017, 12))

    with pytest.raises(FechamentoForaDeSequencia):
        repositorio.fechar(Competencia(2017, 11))


def test_erro_nao_altera_o_fechamento_nem_descarta_a_sessao(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio.fechar(Competencia(2017, 12))

    with pytest.raises(FechamentoForaDeSequencia):
        repositorio.fechar(Competencia(2018, 3))

    assert repositorio.ultima_competencia_fechada() == Competencia(2017, 12)

    repositorio.fechar(Competencia(2018, 1))

    assert repositorio.ultima_competencia_fechada() == Competencia(2018, 1)


def test_rejeita_empresa_inexistente(sessao):
    repositorio = RepositorioFechamento(sessao, 999)

    with pytest.raises(EmpresaInexistente):
        repositorio.fechar(Competencia(2017, 12))


def test_sem_fechamento_nenhuma_competencia_esta_fechada(sessao):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))

    assert repositorio.esta_fechada(Competencia(2017, 12)) is False


@pytest.mark.parametrize(
    ("ano", "mes", "esperado"),
    [
        (2017, 12, True),
        (2017, 1, True),
        (2016, 12, True),
        (2018, 1, False),
        (2018, 12, False),
    ],
)
def test_esta_fechada_ate_a_ultima_competencia_fechada(sessao, ano, mes, esperado):
    repositorio = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio.fechar(Competencia(2017, 12))

    assert repositorio.esta_fechada(Competencia(ano, mes)) is esperado


def test_fechamento_de_uma_empresa_nao_fecha_a_outra(sessao):
    repositorio_a = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio_b = RepositorioFechamento(
        sessao, _nova_empresa(sessao, cnpj="98765432000198")
    )
    repositorio_a.fechar(Competencia(2017, 12))

    assert repositorio_b.ultima_competencia_fechada() is None
    assert repositorio_b.esta_fechada(Competencia(2017, 12)) is False


def test_cada_empresa_tem_o_proprio_primeiro_fechamento(sessao):
    repositorio_a = RepositorioFechamento(sessao, _nova_empresa(sessao))
    repositorio_b = RepositorioFechamento(
        sessao, _nova_empresa(sessao, cnpj="98765432000198")
    )
    repositorio_a.fechar(Competencia(2017, 12))

    repositorio_b.fechar(Competencia(2020, 3))

    assert repositorio_a.ultima_competencia_fechada() == Competencia(2017, 12)
    assert repositorio_b.ultima_competencia_fechada() == Competencia(2020, 3)
