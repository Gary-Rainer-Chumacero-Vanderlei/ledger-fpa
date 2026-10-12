import pytest

from ledger_fpa.domain.conta_contabil import ContaContabil, Natureza, TipoConta


def _conta(**campos):
    dados = {
        "codigo": "1.1.01.001",
        "nome": "Caixa Geral",
        "natureza": Natureza.DEVEDORA,
        "tipo": TipoConta.ANALITICA,
    }
    dados.update(campos)
    return ContaContabil(**dados)


def test_cria_conta_analitica_com_dados_validos():
    conta = ContaContabil(
        codigo="1.1.01.001",
        nome="Caixa Geral",
        natureza=Natureza.DEVEDORA,
        tipo=TipoConta.ANALITICA,
        codigo_pai="1.1.01",
    )

    assert conta.codigo == "1.1.01.001"
    assert conta.nome == "Caixa Geral"
    assert conta.codigo_pai == "1.1.01"


def test_cria_conta_raiz_sem_conta_pai():
    conta = _conta(codigo="1", nome="Ativo", tipo=TipoConta.SINTETICA)

    assert conta.codigo_pai is None


def test_rejeita_nome_vazio():
    with pytest.raises(ValueError):
        _conta(nome="")


def test_rejeita_nome_so_com_espacos():
    with pytest.raises(ValueError):
        _conta(nome="   ")


def test_rejeita_codigo_vazio():
    with pytest.raises(ValueError):
        _conta(codigo="")


def test_rejeita_codigo_com_letras():
    with pytest.raises(ValueError):
        _conta(codigo="1.A.01")


def test_rejeita_codigo_com_ponto_no_fim():
    with pytest.raises(ValueError):
        _conta(codigo="1.1.")


def test_conta_analitica_aceita_lancamento():
    conta = _conta(tipo=TipoConta.ANALITICA)

    assert conta.aceita_lancamento is True


def test_conta_sintetica_nao_aceita_lancamento():
    conta = _conta(tipo=TipoConta.SINTETICA)

    assert conta.aceita_lancamento is False


def test_rejeita_codigo_que_nao_descende_do_pai():
    with pytest.raises(ValueError):
        _conta(codigo="2.1.01.001", codigo_pai="1.1.01")


def test_rejeita_codigo_igual_ao_do_pai():
    with pytest.raises(ValueError):
        _conta(codigo="1.1.01", codigo_pai="1.1.01")


def test_rejeita_pai_que_so_compartilha_prefixo_de_texto():
    with pytest.raises(ValueError):
        _conta(codigo="1.10.01", codigo_pai="1.1")
