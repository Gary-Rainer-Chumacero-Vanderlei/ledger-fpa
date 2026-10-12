import pytest
from ledger_fpa.domain.cnpj import cnpj_valido


@pytest.mark.parametrize(
    "cnpj",
    ["12345678000195", "00000000000191", "12ABC34501DE35"],
)
def test_aceita_cnpj_com_digitos_corretos(cnpj):
    assert cnpj_valido(cnpj) is True


def test_rejeita_primeiro_digito_errado():
    assert cnpj_valido("12345678000185") is False


def test_rejeita_segundo_digito_errado():
    assert cnpj_valido("12345678000196") is False


def test_rejeita_digito_errado_em_cnpj_alfanumerico():
    assert cnpj_valido("12ABC34501DE36") is False


@pytest.mark.parametrize("cnpj", ["00000000000000", "99999999999999"])
def test_rejeita_sequencia_de_caracteres_repetidos(cnpj):
    assert cnpj_valido(cnpj) is False


@pytest.mark.parametrize("cnpj", ["", "123"])
def test_rejeita_tamanho_invalido(cnpj):
    assert cnpj_valido(cnpj) is False


@pytest.mark.parametrize("cnpj", ["12345678@00195", "1234567800019A"])
def test_rejeita_caracteres_invalidos(cnpj):
    assert cnpj_valido(cnpj) is False


def test_rejeita_letras_minusculas():
    assert cnpj_valido("12abc34501de35") is False
