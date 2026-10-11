from datetime import date
from decimal import Decimal

import pytest
from ledger_fpa.domain.lancamento import Lancamento

from ledger_fpa.domain.conta_contabil import ContaContabil, Natureza, TipoConta
from ledger_fpa.domain.partida_lancamento import PartidaLancamento, TipoPartida


def _partida(tipo, valor):
    conta = ContaContabil(
        codigo="1.1.01.001",
        nome="Caixa Geral",
        natureza=Natureza.DEVEDORA,
        tipo=TipoConta.ANALITICA,
    )
    return PartidaLancamento(conta=conta, tipo=tipo, valor=Decimal(valor))


def _lancamento(**campos):
    dados = {
        "data": date(2026, 10, 10),
        "lote": 1,
        "historico": "Prestação de serviços",
        "partidas": (
            _partida(TipoPartida.DEBITO, "100.00"),
            _partida(TipoPartida.CREDITO, "100.00"),
        ),
    }
    dados.update(campos)
    return Lancamento(**dados)


def test_cria_lancamento_balanceado():
    lancamento = _lancamento()

    assert lancamento.lote == 1
    assert lancamento.historico == "Prestação de serviços"
    assert len(lancamento.partidas) == 2


def test_aceita_lancamento_composto_balanceado():
    lancamento = _lancamento(
        partidas=(
            _partida(TipoPartida.DEBITO, "60.00"),
            _partida(TipoPartida.DEBITO, "40.00"),
            _partida(TipoPartida.CREDITO, "100.00"),
        )
    )

    assert len(lancamento.partidas) == 3


def test_soma_com_centavos_nao_gera_erro_de_arredondamento():
    lancamento = _lancamento(
        partidas=(
            _partida(TipoPartida.DEBITO, "0.10"),
            _partida(TipoPartida.DEBITO, "0.20"),
            _partida(TipoPartida.CREDITO, "0.30"),
        )
    )

    assert len(lancamento.partidas) == 3


def test_converte_lista_de_partidas_em_tupla():
    partidas = [
        _partida(TipoPartida.DEBITO, "100.00"),
        _partida(TipoPartida.CREDITO, "100.00"),
    ]

    lancamento = _lancamento(partidas=partidas)

    assert isinstance(lancamento.partidas, tuple)


def test_rejeita_debitos_diferentes_de_creditos():
    with pytest.raises(ValueError):
        _lancamento(
            partidas=(
                _partida(TipoPartida.DEBITO, "100.00"),
                _partida(TipoPartida.CREDITO, "90.00"),
            )
        )


def test_rejeita_lancamento_sem_partidas():
    with pytest.raises(ValueError):
        _lancamento(partidas=())


def test_rejeita_lancamento_somente_com_debitos():
    with pytest.raises(ValueError):
        _lancamento(
            partidas=(
                _partida(TipoPartida.DEBITO, "50.00"),
                _partida(TipoPartida.DEBITO, "50.00"),
            )
        )


def test_rejeita_historico_vazio():
    with pytest.raises(ValueError):
        _lancamento(historico="")


def test_rejeita_historico_so_com_espacos():
    with pytest.raises(ValueError):
        _lancamento(historico="   ")


def test_rejeita_lote_zero():
    with pytest.raises(ValueError):
        _lancamento(lote=0)


def test_rejeita_lote_negativo():
    with pytest.raises(ValueError):
        _lancamento(lote=-1)
