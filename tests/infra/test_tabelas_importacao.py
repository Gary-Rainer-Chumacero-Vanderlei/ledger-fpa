from datetime import date

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ledger_fpa.domain.conta_contabil import Natureza, TipoConta
from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.tabelas import (
    Base,
    ContaContabilTabela,
    EmpresaTabela,
    LancamentoTabela,
    TransacaoImportadaTabela,
)


@pytest.fixture
def engine():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _empresa(sessao, cnpj="12345678000195"):
    empresa = EmpresaTabela(razao_social="Exemplo Ltda", cnpj=cnpj)
    sessao.add(empresa)
    sessao.flush()
    return empresa


def _conta_do_banco(sessao, empresa, codigo="1.1.01.001"):
    conta = ContaContabilTabela(
        empresa_id=empresa.id,
        codigo=codigo,
        nome="Banco",
        natureza=Natureza.DEVEDORA,
        tipo=TipoConta.ANALITICA,
    )
    sessao.add(conta)
    sessao.flush()
    return conta


def _lancamento(sessao, empresa, lote=1):
    lancamento = LancamentoTabela(
        empresa_id=empresa.id,
        data=date(2017, 12, 2),
        lote=lote,
        historico="Compra com cartão",
    )
    sessao.add(lancamento)
    sessao.flush()
    return lancamento


def _registro(empresa, conta, lancamento, **campos):
    dados = {
        "empresa_id": empresa.id,
        "conta_id": conta.id,
        "lancamento_id": lancamento.id,
        "identificador": "20171202001",
    }
    dados.update(campos)
    return TransacaoImportadaTabela(**dados)


def test_cria_tabela_transacao_importada(engine):
    assert "transacao_importada" in inspect(engine).get_table_names()


def test_persiste_e_le_o_registro(engine):
    with Session(engine) as sessao:
        empresa = _empresa(sessao)
        conta = _conta_do_banco(sessao, empresa)
        lancamento = _lancamento(sessao, empresa)
        sessao.add(_registro(empresa, conta, lancamento))
        sessao.commit()

        registro = sessao.scalars(select(TransacaoImportadaTabela)).one()

        assert registro.id is not None
        assert registro.identificador == "20171202001"
        assert registro.lancamento_id == lancamento.id


def test_rejeita_o_mesmo_identificador_na_mesma_empresa_e_conta(engine):
    with Session(engine) as sessao:
        empresa = _empresa(sessao)
        conta = _conta_do_banco(sessao, empresa)
        primeiro = _lancamento(sessao, empresa, lote=1)
        segundo = _lancamento(sessao, empresa, lote=2)
        sessao.add(_registro(empresa, conta, primeiro))
        sessao.commit()

        sessao.add(_registro(empresa, conta, segundo))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_aceita_identificadores_diferentes_na_mesma_conta(engine):
    with Session(engine) as sessao:
        empresa = _empresa(sessao)
        conta = _conta_do_banco(sessao, empresa)
        primeiro = _lancamento(sessao, empresa, lote=1)
        segundo = _lancamento(sessao, empresa, lote=2)
        sessao.add(_registro(empresa, conta, primeiro, identificador="A1"))
        sessao.add(_registro(empresa, conta, segundo, identificador="A2"))
        sessao.commit()

        assert len(sessao.scalars(select(TransacaoImportadaTabela)).all()) == 2


def test_aceita_o_mesmo_identificador_em_outra_conta_do_banco(engine):
    with Session(engine) as sessao:
        empresa = _empresa(sessao)
        banco_a = _conta_do_banco(sessao, empresa, codigo="1.1.01.001")
        banco_b = _conta_do_banco(sessao, empresa, codigo="1.1.01.002")
        primeiro = _lancamento(sessao, empresa, lote=1)
        segundo = _lancamento(sessao, empresa, lote=2)
        sessao.add(_registro(empresa, banco_a, primeiro))
        sessao.add(_registro(empresa, banco_b, segundo))
        sessao.commit()

        assert len(sessao.scalars(select(TransacaoImportadaTabela)).all()) == 2


def test_aceita_o_mesmo_identificador_em_outra_empresa(engine):
    with Session(engine) as sessao:
        empresa_a = _empresa(sessao)
        empresa_b = _empresa(sessao, cnpj="98765432000198")
        conta_a = _conta_do_banco(sessao, empresa_a)
        conta_b = _conta_do_banco(sessao, empresa_b)
        lancamento_a = _lancamento(sessao, empresa_a)
        lancamento_b = _lancamento(sessao, empresa_b)
        sessao.add(_registro(empresa_a, conta_a, lancamento_a))
        sessao.add(_registro(empresa_b, conta_b, lancamento_b))
        sessao.commit()

        assert len(sessao.scalars(select(TransacaoImportadaTabela)).all()) == 2


@pytest.mark.parametrize("campo", ["empresa_id", "conta_id", "lancamento_id"])
def test_rejeita_referencia_inexistente(engine, campo):
    with Session(engine) as sessao:
        empresa = _empresa(sessao)
        conta = _conta_do_banco(sessao, empresa)
        lancamento = _lancamento(sessao, empresa)
        sessao.add(_registro(empresa, conta, lancamento, **{campo: 999}))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_rejeita_identificador_vazio(engine):
    with Session(engine) as sessao:
        empresa = _empresa(sessao)
        conta = _conta_do_banco(sessao, empresa)
        lancamento = _lancamento(sessao, empresa)
        sessao.add(_registro(empresa, conta, lancamento, identificador=""))

        with pytest.raises(IntegrityError):
            sessao.commit()
