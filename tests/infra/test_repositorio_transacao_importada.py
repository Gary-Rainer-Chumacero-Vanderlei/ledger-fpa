from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger_fpa.domain.conta_contabil import ContaContabil, Natureza, TipoConta
from ledger_fpa.domain.empresa import Empresa
from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.repositorio_conta_contabil import (
    EmpresaInexistente,
    RepositorioContaContabil,
)
from ledger_fpa.infra.repositorio_empresa import RepositorioEmpresa
from ledger_fpa.infra.repositorio_transacao_importada import (
    ContaDoBancoInexistente,
    LancamentoInexistente,
    RepositorioTransacaoImportada,
    TransacaoJaImportada,
)
from ledger_fpa.infra.tabelas import Base, LancamentoTabela, TransacaoImportadaTabela


@pytest.fixture
def sessao():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as sessao:
        yield sessao


def _empresa(sessao, cnpj="12345678000195"):
    empresa = Empresa(razao_social="Exemplo Ltda", cnpj=cnpj)
    return RepositorioEmpresa(sessao).adicionar(empresa)


def _banco(sessao, empresa_id, codigo="1.1.01.001"):
    conta = ContaContabil(
        codigo=codigo,
        nome="Banco",
        natureza=Natureza.DEVEDORA,
        tipo=TipoConta.ANALITICA,
    )
    return RepositorioContaContabil(sessao, empresa_id).adicionar(conta)


def _lancamento(sessao, empresa_id, lote=1):
    lancamento = LancamentoTabela(
        empresa_id=empresa_id,
        data=date(2017, 12, 2),
        lote=lote,
        historico="Compra com cartão",
    )
    sessao.add(lancamento)
    sessao.flush()
    return lancamento.id


def _cenario(sessao, cnpj="12345678000195"):
    empresa_id = _empresa(sessao, cnpj)
    conta_id = _banco(sessao, empresa_id)
    repositorio = RepositorioTransacaoImportada(sessao, empresa_id, conta_id)
    return empresa_id, conta_id, repositorio


def test_sem_registros_nenhuma_transacao_foi_importada(sessao):
    _empresa_id, _conta_id, repositorio = _cenario(sessao)

    assert repositorio.ja_importadas(["A1", "A2"]) == set()


def test_registra_e_depois_informa_como_importada(sessao):
    empresa_id, _conta_id, repositorio = _cenario(sessao)

    repositorio.registrar("A1", _lancamento(sessao, empresa_id))

    assert repositorio.ja_importadas(["A1"]) == {"A1"}


def test_devolve_so_os_identificadores_ja_registrados(sessao):
    empresa_id, _conta_id, repositorio = _cenario(sessao)
    repositorio.registrar("A1", _lancamento(sessao, empresa_id, lote=1))
    repositorio.registrar("A2", _lancamento(sessao, empresa_id, lote=2))

    assert repositorio.ja_importadas(["A1", "A3"]) == {"A1"}


def test_lista_vazia_de_identificadores_devolve_conjunto_vazio(sessao):
    _empresa_id, _conta_id, repositorio = _cenario(sessao)

    assert repositorio.ja_importadas([]) == set()


def test_aceita_qualquer_iteravel_de_identificadores(sessao):
    empresa_id, _conta_id, repositorio = _cenario(sessao)
    repositorio.registrar("A1", _lancamento(sessao, empresa_id))

    assert repositorio.ja_importadas(i for i in ["A1", "A1", "A2"]) == {"A1"}


def test_rejeita_identificador_ja_registrado(sessao):
    empresa_id, _conta_id, repositorio = _cenario(sessao)
    repositorio.registrar("A1", _lancamento(sessao, empresa_id, lote=1))

    with pytest.raises(TransacaoJaImportada):
        repositorio.registrar("A1", _lancamento(sessao, empresa_id, lote=2))


def test_erro_de_duplicidade_nao_grava_nem_descarta_a_sessao(sessao):
    empresa_id, _conta_id, repositorio = _cenario(sessao)
    repositorio.registrar("A1", _lancamento(sessao, empresa_id, lote=1))

    with pytest.raises(TransacaoJaImportada):
        repositorio.registrar("A1", _lancamento(sessao, empresa_id, lote=2))

    assert len(sessao.scalars(select(TransacaoImportadaTabela)).all()) == 1

    repositorio.registrar("A2", _lancamento(sessao, empresa_id, lote=3))

    assert repositorio.ja_importadas(["A1", "A2"]) == {"A1", "A2"}


def test_aceita_o_mesmo_identificador_em_outra_conta_do_banco(sessao):
    empresa_id, _conta_id, repositorio_a = _cenario(sessao)
    outra_conta = _banco(sessao, empresa_id, codigo="1.1.01.002")
    repositorio_b = RepositorioTransacaoImportada(sessao, empresa_id, outra_conta)
    repositorio_a.registrar("A1", _lancamento(sessao, empresa_id, lote=1))

    repositorio_b.registrar("A1", _lancamento(sessao, empresa_id, lote=2))

    assert repositorio_b.ja_importadas(["A1"]) == {"A1"}


def test_aceita_o_mesmo_identificador_em_outra_empresa(sessao):
    empresa_a, _conta_a, repositorio_a = _cenario(sessao)
    empresa_b, _conta_b, repositorio_b = _cenario(sessao, cnpj="98765432000198")
    repositorio_a.registrar("A1", _lancamento(sessao, empresa_a))

    repositorio_b.registrar("A1", _lancamento(sessao, empresa_b))

    assert repositorio_b.ja_importadas(["A1"]) == {"A1"}


def test_a_consulta_nao_enxerga_outra_conta_do_banco(sessao):
    empresa_id, _conta_id, repositorio_a = _cenario(sessao)
    outra_conta = _banco(sessao, empresa_id, codigo="1.1.01.002")
    repositorio_b = RepositorioTransacaoImportada(sessao, empresa_id, outra_conta)
    repositorio_a.registrar("A1", _lancamento(sessao, empresa_id))

    assert repositorio_b.ja_importadas(["A1"]) == set()


def test_a_consulta_nao_enxerga_outra_empresa(sessao):
    empresa_a, _conta_a, repositorio_a = _cenario(sessao)
    _empresa_b, _conta_b, repositorio_b = _cenario(sessao, cnpj="98765432000198")
    repositorio_a.registrar("A1", _lancamento(sessao, empresa_a))

    assert repositorio_b.ja_importadas(["A1"]) == set()


def test_a_consulta_filtra_pela_empresa_mesmo_com_conta_de_outra(sessao):
    empresa_a, conta_a, repositorio_a = _cenario(sessao)
    empresa_b = _empresa(sessao, cnpj="98765432000198")
    repositorio_a.registrar("A1", _lancamento(sessao, empresa_a))
    repositorio_b = RepositorioTransacaoImportada(sessao, empresa_b, conta_a)

    assert repositorio_b.ja_importadas(["A1"]) == set()


def test_rejeita_empresa_inexistente(sessao):
    empresa_id, conta_id, _repositorio = _cenario(sessao)
    lancamento_id = _lancamento(sessao, empresa_id)
    repositorio = RepositorioTransacaoImportada(sessao, 999, conta_id)

    with pytest.raises(EmpresaInexistente):
        repositorio.registrar("A1", lancamento_id)


def test_rejeita_conta_do_banco_inexistente(sessao):
    empresa_id = _empresa(sessao)
    lancamento_id = _lancamento(sessao, empresa_id)
    repositorio = RepositorioTransacaoImportada(sessao, empresa_id, 999)

    with pytest.raises(ContaDoBancoInexistente):
        repositorio.registrar("A1", lancamento_id)


def test_rejeita_conta_do_banco_de_outra_empresa(sessao):
    _empresa_a, conta_a, _repositorio_a = _cenario(sessao)
    empresa_b = _empresa(sessao, cnpj="98765432000198")
    lancamento_id = _lancamento(sessao, empresa_b)
    repositorio = RepositorioTransacaoImportada(sessao, empresa_b, conta_a)

    with pytest.raises(ContaDoBancoInexistente):
        repositorio.registrar("A1", lancamento_id)


def test_rejeita_lancamento_inexistente_sem_gravar_nada(sessao):
    _empresa_id, _conta_id, repositorio = _cenario(sessao)

    with pytest.raises(LancamentoInexistente):
        repositorio.registrar("A1", 999)

    assert repositorio.ja_importadas(["A1"]) == set()


def test_rejeita_lancamento_de_outra_empresa(sessao):
    _empresa_a, _conta_a, repositorio_a = _cenario(sessao)
    empresa_b = _empresa(sessao, cnpj="98765432000198")
    lancamento_b = _lancamento(sessao, empresa_b)

    with pytest.raises(LancamentoInexistente):
        repositorio_a.registrar("A1", lancamento_b)


@pytest.mark.parametrize("identificador", ["", "   "])
def test_rejeita_identificador_vazio(sessao, identificador):
    empresa_id, _conta_id, repositorio = _cenario(sessao)

    with pytest.raises(ValueError):
        repositorio.registrar(identificador, _lancamento(sessao, empresa_id))
