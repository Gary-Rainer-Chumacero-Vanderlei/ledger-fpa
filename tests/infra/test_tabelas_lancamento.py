from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ledger_fpa.domain.conta_contabil import Natureza, TipoConta
from ledger_fpa.domain.partida_lancamento import TipoPartida
from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.dinheiro import de_centavos, para_centavos
from ledger_fpa.infra.tabelas import (
    Base,
    ContaContabilTabela,
    EmpresaTabela,
    LancamentoTabela,
    PartidaLancamentoTabela,
)


@pytest.fixture
def engine():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _empresa(**campos):
    dados = {"razao_social": "Exemplo Ltda", "cnpj": "12345678000195"}
    dados.update(campos)
    return EmpresaTabela(**dados)


def _conta(empresa_id):
    return ContaContabilTabela(
        empresa_id=empresa_id,
        codigo="1.1.01.001",
        nome="Caixa Geral",
        natureza=Natureza.DEVEDORA,
        tipo=TipoConta.ANALITICA,
    )


def _lancamento(empresa_id, **campos):
    dados = {
        "empresa_id": empresa_id,
        "data": date(2026, 10, 10),
        "lote": 1,
        "historico": "Prestação de serviços",
    }
    dados.update(campos)
    return LancamentoTabela(**dados)


def _partida(lancamento_id, conta_id, **campos):
    dados = {
        "lancamento_id": lancamento_id,
        "conta_id": conta_id,
        "tipo": TipoPartida.DEBITO,
        "valor_centavos": 10050,
    }
    dados.update(campos)
    return PartidaLancamentoTabela(**dados)


def _base(sessao):
    empresa = _empresa()
    sessao.add(empresa)
    sessao.flush()

    conta = _conta(empresa.id)
    sessao.add(conta)
    sessao.flush()

    return empresa, conta


def test_cria_tabelas_lancamento_e_partida_lancamento(engine):
    tabelas = inspect(engine).get_table_names()

    assert "lancamento" in tabelas
    assert "partida_lancamento" in tabelas


def test_persiste_lancamento_com_partidas(engine):
    with Session(engine) as sessao:
        empresa, conta = _base(sessao)
        lancamento = _lancamento(empresa.id)
        sessao.add(lancamento)
        sessao.flush()

        sessao.add(_partida(lancamento.id, conta.id, tipo=TipoPartida.DEBITO))
        sessao.add(_partida(lancamento.id, conta.id, tipo=TipoPartida.CREDITO))
        sessao.commit()

        partidas = sessao.scalars(select(PartidaLancamentoTabela)).all()

        assert len(partidas) == 2


def test_valor_volta_do_banco_como_decimal_exato(engine):
    with Session(engine) as sessao:
        empresa, conta = _base(sessao)
        lancamento = _lancamento(empresa.id)
        sessao.add(lancamento)
        sessao.flush()

        sessao.add(
            _partida(
                lancamento.id,
                conta.id,
                valor_centavos=para_centavos(Decimal("100.50")),
            )
        )
        sessao.commit()

        partida = sessao.scalars(select(PartidaLancamentoTabela)).one()

        assert de_centavos(partida.valor_centavos) == Decimal("100.50")


def test_rejeita_lancamento_com_empresa_inexistente(engine):
    with Session(engine) as sessao:
        sessao.add(_lancamento(empresa_id=999))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_rejeita_lote_duplicado_na_mesma_empresa(engine):
    with Session(engine) as sessao:
        empresa, _conta_base = _base(sessao)
        sessao.add(_lancamento(empresa.id))
        sessao.add(_lancamento(empresa.id, historico="Outro histórico"))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_aceita_mesmo_lote_em_empresas_diferentes(engine):
    with Session(engine) as sessao:
        empresa_a, _conta_base = _base(sessao)
        empresa_b = _empresa(cnpj="98765432000100")
        sessao.add(empresa_b)
        sessao.flush()

        sessao.add(_lancamento(empresa_a.id))
        sessao.add(_lancamento(empresa_b.id))
        sessao.commit()

        lancamentos = sessao.scalars(select(LancamentoTabela)).all()

        assert len(lancamentos) == 2


def test_rejeita_partida_com_lancamento_inexistente(engine):
    with Session(engine) as sessao:
        _empresa_base, conta = _base(sessao)
        sessao.add(_partida(lancamento_id=999, conta_id=conta.id))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_rejeita_partida_com_conta_inexistente(engine):
    with Session(engine) as sessao:
        empresa, _conta_base = _base(sessao)
        lancamento = _lancamento(empresa.id)
        sessao.add(lancamento)
        sessao.flush()

        sessao.add(_partida(lancamento.id, conta_id=999))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_rejeita_partida_com_valor_zero(engine):
    with Session(engine) as sessao:
        empresa, conta = _base(sessao)
        lancamento = _lancamento(empresa.id)
        sessao.add(lancamento)
        sessao.flush()

        sessao.add(_partida(lancamento.id, conta.id, valor_centavos=0))

        with pytest.raises(IntegrityError):
            sessao.commit()


def test_rejeita_partida_com_valor_negativo(engine):
    with Session(engine) as sessao:
        empresa, conta = _base(sessao)
        lancamento = _lancamento(empresa.id)
        sessao.add(lancamento)
        sessao.flush()

        sessao.add(_partida(lancamento.id, conta.id, valor_centavos=-1))

        with pytest.raises(IntegrityError):
            sessao.commit()
