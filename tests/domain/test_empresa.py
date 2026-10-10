import pytest

from ledger_fpa.domain.empresa import Empresa


def test_cria_empresa_com_dados_validos():
    empresa = Empresa(razao_social="Exemplo Ltda", cnpj="12.345.678/0001-95")

    assert empresa.razao_social == "Exemplo Ltda"
    assert empresa.cnpj == "12345678000195"


def test_rejeita_razao_social_vazia():
    with pytest.raises(ValueError):
        Empresa(razao_social="", cnpj="12.345.678/0001-95")


def test_rejeita_razao_social_so_com_espacos():
    with pytest.raises(ValueError):
        Empresa(razao_social="   ", cnpj="12.345.678/0001-95")


def test_normaliza_cnpj_para_maiusculas():
    empresa = Empresa(razao_social="Exemplo Ltda", cnpj="ab.cde.fgh/0001-12")

    assert empresa.cnpj == "ABCDEFGH000112"


def test_rejeita_cnpj_com_tamanho_invalido():
    with pytest.raises(ValueError):
        Empresa(razao_social="Exemplo Ltda", cnpj="123")


def test_rejeita_cnpj_com_caracteres_invalidos():
    with pytest.raises(ValueError):
        Empresa(razao_social="Exemplo Ltda", cnpj="12.345.678/00@1-95")
