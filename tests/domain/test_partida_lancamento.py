from decimal import Decimal

import pytest

from ledger_fpa.domain.conta_contabil import ContaContabil, Natureza, TipoConta
from ledger_fpa.domain.partida_lancamento import PartidaLancamento, TipoPartida


def _conta(tipo=TipoConta.ANALITICA):
    return ContaContabil(
        codigo="1.1.01.001",
        nome="Caixa Geral",
        natureza=Natureza.DEVEDORA,
        tipo=tipo,
    )


def test_cria_partida_de_debito_com_dados_validos():
    partida = PartidaLancamento(
        conta=_conta(), tipo=TipoPartida.DEBITO, valor=Decimal("100.50")
    )

    assert partida.tipo is TipoPartida.DEBITO
    assert partida.valor == Decimal("100.50")


def test_cria_partida_de_credito():
    partida = PartidaLancamento(
        conta=_conta(), tipo=TipoPartida.CREDITO, valor=Decimal("100.50")
    )

    assert partida.tipo is TipoPartida.CREDITO


def test_rejeita_valor_zero():
    with pytest.raises(ValueError):
        PartidaLancamento(conta=_conta(), tipo=TipoPartida.DEBITO, valor=Decimal("0"))


def test_rejeita_valor_negativo():
    with pytest.raises(ValueError):
        PartidaLancamento(conta=_conta(), tipo=TipoPartida.DEBITO, valor=Decimal("-10"))


def test_rejeita_valor_float():
    with pytest.raises(TypeError):
        PartidaLancamento(conta=_conta(), tipo=TipoPartida.DEBITO, valor=100.5)


def test_rejeita_valor_com_mais_de_duas_casas():
    with pytest.raises(ValueError):
        PartidaLancamento(
            conta=_conta(), tipo=TipoPartida.DEBITO, valor=Decimal("10.123")
        )


def test_aceita_valor_com_uma_casa():
    partida = PartidaLancamento(
        conta=_conta(), tipo=TipoPartida.DEBITO, valor=Decimal("10.5")
    )

    assert partida.valor == Decimal("10.5")


def test_rejeita_conta_sintetica():
    with pytest.raises(ValueError):
        PartidaLancamento(
            conta=_conta(TipoConta.SINTETICA),
            tipo=TipoPartida.DEBITO,
            valor=Decimal("100.50"),
        )
