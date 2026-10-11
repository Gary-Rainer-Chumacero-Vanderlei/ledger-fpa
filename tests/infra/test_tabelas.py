import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ledger_fpa.domain.conta_contabil import Natureza, TipoConta
from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.tabelas import Base, ContaContabilTabela, EmpresaTabela


@pytest.fixture
def engine():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _empresa(**campos):
    dados = {"razao_social": "Exemplo Ltda", "cnpj": "12345678000195"}
    dados.update(campos)
    return EmpresaTabela(**dados)


def _conta(empresa_id, **campos):
    dados = {
        "empresa_id": empresa_id,
        "codigo": "1.1.01.001",
        "nome": "Caixa Geral",
        "natureza": Natureza.DEVEDORA,
        "tipo": TipoConta.ANALITICA,
    }
    dados.update(campos)
    return ContaContabilTabela(**dados)


def test_cria_tabelas_empresa_e_conta_contabil(engine):
    tabelas = inspect(engine).get_table_names()

    assert "empresa" in tabelas
    assert "conta_contabil" in tabelas


def test_persiste_e_le_empresa(engine):
    with Session(engine) as sessao:
        sessao.add(_empresa())
        sessao.commit()

        empresa = sessao.scalars(select(EmpresaTabela)).one()

        assert empresa.id is not None
        assert empresa.cnpj == "12345678000195"


def test_rejeita_cnpj_duplicado(engine):
    with Session(engine) as sessao:
        sessao.add(_empresa())
        sessao.commit()

        sessao.add(_empresa(razao_social="Outra Ltda"))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_rejeita_conta_com_empresa_inexistente(engine):
    with Session(engine) as sessao:
        sessao.add(_conta(empresa_id=999))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_persiste_conta_com_conta_pai(engine):
    with Session(engine) as sessao:
        empresa = _empresa()
        sessao.add(empresa)
        sessao.flush()

        pai = _conta(
            empresa.id,
            codigo="1.1.01",
            nome="Caixa",
            tipo=TipoConta.SINTETICA,
        )
        sessao.add(pai)
        sessao.flush()

        filha = _conta(empresa.id, conta_pai_id=pai.id)
        sessao.add(filha)
        sessao.commit()

        assert filha.conta_pai_id == pai.id


def test_rejeita_conta_pai_inexistente(engine):
    with Session(engine) as sessao:
        empresa = _empresa()
        sessao.add(empresa)
        sessao.flush()

        sessao.add(_conta(empresa.id, conta_pai_id=999))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_rejeita_codigo_duplicado_na_mesma_empresa(engine):
    with Session(engine) as sessao:
        empresa = _empresa()
        sessao.add(empresa)
        sessao.flush()

        sessao.add(_conta(empresa.id))
        sessao.add(_conta(empresa.id, nome="Outro Caixa"))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_aceita_mesmo_codigo_em_empresas_diferentes(engine):
    with Session(engine) as sessao:
        empresa_a = _empresa()
        empresa_b = _empresa(cnpj="98765432000100")
        sessao.add_all([empresa_a, empresa_b])
        sessao.flush()

        sessao.add(_conta(empresa_a.id))
        sessao.add(_conta(empresa_b.id))
        sessao.commit()

        contas = sessao.scalars(select(ContaContabilTabela)).all()

        assert len(contas) == 2
