import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.tabelas import Base, EmpresaTabela, FechamentoTabela


@pytest.fixture
def engine():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _empresa(**campos):
    dados = {"razao_social": "Exemplo Ltda", "cnpj": "12345678000195"}
    dados.update(campos)
    return EmpresaTabela(**dados)


def _fechamento(empresa_id, **campos):
    dados = {"empresa_id": empresa_id, "ano": 2017, "mes": 12}
    dados.update(campos)
    return FechamentoTabela(**dados)


def test_cria_tabela_fechamento(engine):
    assert "fechamento" in inspect(engine).get_table_names()


def test_persiste_e_le_fechamento(engine):
    with Session(engine) as sessao:
        empresa = _empresa()
        sessao.add(empresa)
        sessao.flush()
        sessao.add(_fechamento(empresa.id))
        sessao.commit()

        fechamento = sessao.scalars(select(FechamentoTabela)).one()

        assert fechamento.id is not None
        assert (fechamento.ano, fechamento.mes) == (2017, 12)


def test_rejeita_segundo_fechamento_da_mesma_empresa(engine):
    with Session(engine) as sessao:
        empresa = _empresa()
        sessao.add(empresa)
        sessao.flush()
        sessao.add(_fechamento(empresa.id))
        sessao.commit()

        sessao.add(_fechamento(empresa.id, ano=2018, mes=1))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_aceita_um_fechamento_por_empresa(engine):
    with Session(engine) as sessao:
        empresa_a = _empresa()
        empresa_b = _empresa(cnpj="98765432000198")
        sessao.add_all([empresa_a, empresa_b])
        sessao.flush()
        sessao.add(_fechamento(empresa_a.id))
        sessao.add(_fechamento(empresa_b.id))
        sessao.commit()

        fechamentos = sessao.scalars(select(FechamentoTabela)).all()

        assert len(fechamentos) == 2


def test_rejeita_fechamento_com_empresa_inexistente(engine):
    with Session(engine) as sessao:
        sessao.add(_fechamento(empresa_id=999))

        with pytest.raises(IntegrityError):
            sessao.commit()


@pytest.mark.parametrize("mes", [0, 13])
def test_rejeita_mes_fora_do_intervalo(engine, mes):
    with Session(engine) as sessao:
        empresa = _empresa()
        sessao.add(empresa)
        sessao.flush()
        sessao.add(_fechamento(empresa.id, mes=mes))

        with pytest.raises(IntegrityError):
            sessao.commit()


@pytest.mark.parametrize("ano", [0, 10000])
def test_rejeita_ano_fora_do_intervalo(engine, ano):
    with Session(engine) as sessao:
        empresa = _empresa()
        sessao.add(empresa)
        sessao.flush()
        sessao.add(_fechamento(empresa.id, ano=ano))

        with pytest.raises(IntegrityError):
            sessao.commit()
