from datetime import date

import pytest
from ledger_fpa.domain.competencia import Competencia


def test_cria_competencia_com_dados_validos():
    competencia = Competencia(ano=2026, mes=10)

    assert competencia.ano == 2026
    assert competencia.mes == 10


@pytest.mark.parametrize("mes", [0, 13, -1])
def test_rejeita_mes_fora_do_intervalo(mes):
    with pytest.raises(ValueError):
        Competencia(ano=2026, mes=mes)


@pytest.mark.parametrize("ano", [0, -1, 10000])
def test_rejeita_ano_fora_do_intervalo(ano):
    with pytest.raises(ValueError):
        Competencia(ano=ano, mes=1)


@pytest.mark.parametrize(
    ("ano", "mes"),
    [(2026.5, 10), (2026, 10.5), ("2026", 10), (True, 10)],
)
def test_rejeita_ano_ou_mes_que_nao_sao_inteiros(ano, mes):
    with pytest.raises(TypeError):
        Competencia(ano=ano, mes=mes)


def test_cria_a_partir_de_uma_data():
    assert Competencia.de_data(date(2026, 10, 31)) == Competencia(2026, 10)


def test_proxima_competencia_no_mesmo_ano():
    assert Competencia(2026, 10).proxima() == Competencia(2026, 11)


def test_proxima_competencia_vira_o_ano_em_dezembro():
    assert Competencia(2017, 12).proxima() == Competencia(2018, 1)


def test_proxima_do_ultimo_ano_valido_e_rejeitada():
    with pytest.raises(ValueError):
        Competencia(9999, 12).proxima()


def test_competencias_sao_ordenadas_por_ano_e_mes():
    assert Competencia(2017, 12) < Competencia(2018, 1)
    assert Competencia(2018, 1) < Competencia(2018, 2)
    assert not Competencia(2018, 2) < Competencia(2018, 2)
    assert Competencia(2018, 2) <= Competencia(2018, 2)


def test_texto_no_formato_mes_barra_ano():
    assert str(Competencia(2017, 12)) == "12/2017"
    assert str(Competencia(2018, 1)) == "01/2018"


def test_competencia_e_imutavel():
    competencia = Competencia(2026, 10)

    with pytest.raises(AttributeError):
        competencia.mes = 11
