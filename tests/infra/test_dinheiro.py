from decimal import Decimal

import pytest
from ledger_fpa.infra.dinheiro import de_centavos, para_centavos


def test_converte_reais_para_centavos():
    assert para_centavos(Decimal("100.50")) == 10050


def test_converte_valor_com_uma_casa():
    assert para_centavos(Decimal("10.5")) == 1050


def test_converte_valor_menor_que_um_real():
    assert para_centavos(Decimal("0.10")) == 10


def test_soma_em_centavos_nao_gera_erro_de_arredondamento():
    soma = para_centavos(Decimal("0.10")) + para_centavos(Decimal("0.20"))

    assert soma == para_centavos(Decimal("0.30"))


def test_para_centavos_rejeita_mais_de_duas_casas():
    with pytest.raises(ValueError):
        para_centavos(Decimal("10.123"))


def test_para_centavos_rejeita_float():
    with pytest.raises(TypeError):
        para_centavos(100.5)


def test_converte_centavos_para_reais():
    assert de_centavos(10050) == Decimal("100.50")


def test_converte_centavos_menores_que_um_real_para_reais():
    assert de_centavos(10) == Decimal("0.10")


def test_de_centavos_rejeita_float():
    with pytest.raises(TypeError):
        de_centavos(100.5)


def test_ida_e_volta_preserva_o_valor():
    valor = Decimal("12345.67")

    assert de_centavos(para_centavos(valor)) == valor
