from datetime import date, datetime
from decimal import Decimal

import pytest
from ledger_fpa.domain.transacao_extrato import Sentido, TransacaoExtrato


def _transacao(**campos):
    dados = {
        "data": date(2017, 12, 2),
        "historico": "COMPRA COM CARTÃO",
        "valor": Decimal("83.93"),
        "sentido": Sentido.SUBTRAI,
        "identificador": "20171202001",
    }
    dados.update(campos)
    return TransacaoExtrato(**dados)


def test_cria_transacao_com_dados_validos():
    transacao = _transacao()

    assert transacao.data == date(2017, 12, 2)
    assert transacao.historico == "COMPRA COM CARTÃO"
    assert transacao.valor == Decimal("83.93")
    assert transacao.sentido is Sentido.SUBTRAI
    assert transacao.identificador == "20171202001"
    assert transacao.documento is None


@pytest.mark.parametrize("sentido", [Sentido.SOMA, Sentido.SUBTRAI])
def test_aceita_os_dois_sentidos(sentido):
    assert _transacao(sentido=sentido).sentido is sentido


def test_cria_transacao_com_documento():
    assert _transacao(documento="180880").documento == "180880"


@pytest.mark.parametrize("documento", ["", "   "])
def test_documento_em_branco_vira_none(documento):
    assert _transacao(documento=documento).documento is None


def test_remove_espacos_das_bordas_dos_textos():
    transacao = _transacao(
        historico="  COMPRA COM CARTÃO  ",
        identificador=" 20171202001 ",
        documento=" 180880 ",
    )

    assert transacao.historico == "COMPRA COM CARTÃO"
    assert transacao.identificador == "20171202001"
    assert transacao.documento == "180880"


@pytest.mark.parametrize("historico", ["", "   "])
def test_rejeita_historico_vazio(historico):
    with pytest.raises(ValueError):
        _transacao(historico=historico)


@pytest.mark.parametrize("identificador", ["", "   "])
def test_rejeita_identificador_vazio(identificador):
    with pytest.raises(ValueError):
        _transacao(identificador=identificador)


@pytest.mark.parametrize("valor", [Decimal("0"), Decimal("-1")])
def test_rejeita_valor_zero_ou_negativo(valor):
    with pytest.raises(ValueError):
        _transacao(valor=valor)


@pytest.mark.parametrize("valor", [Decimal("NaN"), Decimal("Infinity")])
def test_rejeita_valor_que_nao_e_finito(valor):
    with pytest.raises(ValueError):
        _transacao(valor=valor)


def test_rejeita_valor_com_mais_de_duas_casas():
    with pytest.raises(ValueError):
        _transacao(valor=Decimal("10.123"))


def test_aceita_valor_com_uma_casa():
    assert _transacao(valor=Decimal("10.5")).valor == Decimal("10.5")


@pytest.mark.parametrize("valor", [100.5, 10])
def test_rejeita_valor_que_nao_e_decimal(valor):
    with pytest.raises(TypeError):
        _transacao(valor=valor)


@pytest.mark.parametrize("data", [datetime(2017, 12, 2, 22, 0), "2017-12-02"])
def test_rejeita_data_que_nao_e_um_date(data):
    with pytest.raises(TypeError):
        _transacao(data=data)


def test_transacao_e_imutavel():
    transacao = _transacao()

    with pytest.raises(AttributeError):
        transacao.valor = Decimal("1.00")


def test_transacoes_com_os_mesmos_dados_sao_iguais():
    assert _transacao() == _transacao()
    assert _transacao() != _transacao(sentido=Sentido.SOMA)
