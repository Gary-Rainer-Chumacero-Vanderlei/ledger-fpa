from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from ledger_fpa.domain.conta_contabil import ContaContabil, Natureza, TipoConta
from ledger_fpa.domain.empresa import Empresa
from ledger_fpa.domain.lancamento import Lancamento
from ledger_fpa.domain.partida_lancamento import PartidaLancamento, TipoPartida
from ledger_fpa.infra.banco import criar_engine
from ledger_fpa.infra.repositorio_conta_contabil import (
    EmpresaInexistente,
    RepositorioContaContabil,
)
from ledger_fpa.infra.repositorio_empresa import RepositorioEmpresa
from ledger_fpa.infra.repositorio_lancamento import (
    ContaInexistente,
    ContaNaoAnalitica,
    LoteJaCadastrado,
    RepositorioLancamento,
)
from ledger_fpa.infra.tabelas import Base, PartidaLancamentoTabela


@pytest.fixture
def sessao():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as sessao:
        yield sessao


def _caixa():
    return ContaContabil(
        codigo="1.1.01.001",
        nome="Caixa Geral",
        natureza=Natureza.DEVEDORA,
        tipo=TipoConta.ANALITICA,
    )


def _receita():
    return ContaContabil(
        codigo="3.1.01.001",
        nome="Serviços Prestados",
        natureza=Natureza.CREDORA,
        tipo=TipoConta.ANALITICA,
    )


def _nova_empresa(sessao, cnpj="12345678000195"):
    empresa = Empresa(razao_social="Exemplo Ltda", cnpj=cnpj)
    return RepositorioEmpresa(sessao).adicionar(empresa)


def _preparar(sessao, cnpj="12345678000195"):
    empresa_id = _nova_empresa(sessao, cnpj)
    contas = RepositorioContaContabil(sessao, empresa_id)
    contas.adicionar(_caixa())
    contas.adicionar(_receita())
    return empresa_id


def _lancamento(**campos):
    dados = {
        "data": date(2026, 10, 10),
        "lote": 1,
        "historico": "Prestação de serviços",
        "partidas": (
            PartidaLancamento(_caixa(), TipoPartida.DEBITO, Decimal("100.50")),
            PartidaLancamento(_receita(), TipoPartida.CREDITO, Decimal("100.50")),
        ),
    }
    dados.update(campos)
    return Lancamento(**dados)


def test_adicionar_devolve_o_id_gerado(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))

    lancamento_id = repositorio.adicionar(_lancamento())

    assert isinstance(lancamento_id, int)


def test_busca_lancamento_por_lote(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))
    repositorio.adicionar(_lancamento())

    assert repositorio.buscar_por_lote(1) == _lancamento()


def test_valores_sao_gravados_em_centavos(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))
    repositorio.adicionar(_lancamento())

    valores = sessao.scalars(select(PartidaLancamentoTabela.valor_centavos)).all()

    assert valores == [10050, 10050]


def test_preserva_a_ordem_das_partidas(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))
    partidas = (
        PartidaLancamento(_receita(), TipoPartida.CREDITO, Decimal("100.50")),
        PartidaLancamento(_caixa(), TipoPartida.DEBITO, Decimal("100.50")),
    )
    repositorio.adicionar(_lancamento(partidas=partidas))

    lancamento = repositorio.buscar_por_lote(1)

    assert lancamento is not None
    assert lancamento.partidas == partidas


def test_valores_com_centavos_voltam_exatos(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))
    partidas = (
        PartidaLancamento(_caixa(), TipoPartida.DEBITO, Decimal("0.10")),
        PartidaLancamento(_caixa(), TipoPartida.DEBITO, Decimal("0.20")),
        PartidaLancamento(_receita(), TipoPartida.CREDITO, Decimal("0.30")),
    )
    repositorio.adicionar(_lancamento(partidas=partidas))

    lancamento = repositorio.buscar_por_lote(1)

    assert lancamento is not None
    valores = [partida.valor for partida in lancamento.partidas]
    assert valores == [Decimal("0.10"), Decimal("0.20"), Decimal("0.30")]


def test_partida_volta_com_a_conta_e_o_codigo_do_pai(sessao):
    empresa_id = _nova_empresa(sessao)
    contas = RepositorioContaContabil(sessao, empresa_id)
    contas.adicionar(
        ContaContabil(
            codigo="1.1.01",
            nome="Caixa",
            natureza=Natureza.DEVEDORA,
            tipo=TipoConta.SINTETICA,
        )
    )
    caixa = ContaContabil(
        codigo="1.1.01.001",
        nome="Caixa Geral",
        natureza=Natureza.DEVEDORA,
        tipo=TipoConta.ANALITICA,
        codigo_pai="1.1.01",
    )
    contas.adicionar(caixa)
    contas.adicionar(_receita())
    partidas = (
        PartidaLancamento(caixa, TipoPartida.DEBITO, Decimal("100.50")),
        PartidaLancamento(_receita(), TipoPartida.CREDITO, Decimal("100.50")),
    )
    repositorio = RepositorioLancamento(sessao, empresa_id)
    repositorio.adicionar(_lancamento(partidas=partidas))

    assert repositorio.buscar_por_lote(1) == _lancamento(partidas=partidas)


def test_rejeita_lote_duplicado_na_mesma_empresa(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))
    repositorio.adicionar(_lancamento())

    with pytest.raises(LoteJaCadastrado):
        repositorio.adicionar(_lancamento(historico="Outro histórico"))


def test_aceita_mesmo_lote_em_empresas_diferentes(sessao):
    repositorio_a = RepositorioLancamento(sessao, _preparar(sessao))
    repositorio_b = RepositorioLancamento(
        sessao, _preparar(sessao, cnpj="98765432000198")
    )
    repositorio_a.adicionar(_lancamento())

    lancamento_id = repositorio_b.adicionar(_lancamento())

    assert isinstance(lancamento_id, int)


def test_rejeita_empresa_inexistente(sessao):
    repositorio = RepositorioLancamento(sessao, 999)

    with pytest.raises(EmpresaInexistente):
        repositorio.adicionar(_lancamento())


def test_rejeita_conta_inexistente(sessao):
    repositorio = RepositorioLancamento(sessao, _nova_empresa(sessao))

    with pytest.raises(ContaInexistente):
        repositorio.adicionar(_lancamento())


def test_rejeita_conta_de_outra_empresa(sessao):
    _preparar(sessao)
    empresa_b = _nova_empresa(sessao, cnpj="98765432000198")
    repositorio_b = RepositorioLancamento(sessao, empresa_b)

    with pytest.raises(ContaInexistente):
        repositorio_b.adicionar(_lancamento())


def test_rejeita_conta_que_no_banco_nao_e_analitica(sessao):
    empresa_id = _nova_empresa(sessao)
    contas = RepositorioContaContabil(sessao, empresa_id)
    contas.adicionar(
        ContaContabil(
            codigo="1.1.01.001",
            nome="Caixa Geral",
            natureza=Natureza.DEVEDORA,
            tipo=TipoConta.SINTETICA,
        )
    )
    contas.adicionar(_receita())
    repositorio = RepositorioLancamento(sessao, empresa_id)

    with pytest.raises(ContaNaoAnalitica):
        repositorio.adicionar(_lancamento())


def test_nada_e_gravado_quando_uma_conta_nao_existe(sessao):
    empresa_id = _nova_empresa(sessao)
    RepositorioContaContabil(sessao, empresa_id).adicionar(_caixa())
    repositorio = RepositorioLancamento(sessao, empresa_id)

    with pytest.raises(ContaInexistente):
        repositorio.adicionar(_lancamento())

    assert repositorio.buscar_por_lote(1) is None
    assert sessao.scalars(select(PartidaLancamentoTabela)).all() == []


def test_erro_nao_descarta_o_trabalho_anterior(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))
    repositorio.adicionar(_lancamento())

    with pytest.raises(LoteJaCadastrado):
        repositorio.adicionar(_lancamento(historico="Outro histórico"))

    assert repositorio.buscar_por_lote(1) is not None
    assert isinstance(repositorio.adicionar(_lancamento(lote=2)), int)


def test_busca_por_lote_inexistente_devolve_none(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))

    assert repositorio.buscar_por_lote(999) is None


def test_busca_nao_enxerga_lancamento_de_outra_empresa(sessao):
    repositorio_a = RepositorioLancamento(sessao, _preparar(sessao))
    repositorio_b = RepositorioLancamento(
        sessao, _preparar(sessao, cnpj="98765432000198")
    )
    repositorio_a.adicionar(_lancamento())

    assert repositorio_b.buscar_por_lote(1) is None


def test_lista_devolve_os_lancamentos_com_as_partidas(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))
    primeiro = _lancamento(lote=1)
    segundo = _lancamento(lote=2, historico="Outro histórico")
    repositorio.adicionar(primeiro)
    repositorio.adicionar(segundo)

    assert repositorio.listar() == [primeiro, segundo]


def test_lista_lancamentos_ordenados_por_data_e_lote(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))
    repositorio.adicionar(_lancamento(lote=3, data=date(2026, 10, 12)))
    repositorio.adicionar(_lancamento(lote=1, data=date(2026, 10, 12)))
    repositorio.adicionar(_lancamento(lote=2, data=date(2026, 10, 5)))

    lotes = [lancamento.lote for lancamento in repositorio.listar()]

    assert lotes == [2, 1, 3]


def test_lista_somente_lancamentos_da_empresa(sessao):
    repositorio_a = RepositorioLancamento(sessao, _preparar(sessao))
    repositorio_b = RepositorioLancamento(
        sessao, _preparar(sessao, cnpj="98765432000198")
    )
    repositorio_a.adicionar(_lancamento(lote=1))
    repositorio_b.adicionar(_lancamento(lote=2))

    lotes = [lancamento.lote for lancamento in repositorio_b.listar()]

    assert lotes == [2]


def test_lista_vazia_quando_nao_ha_lancamentos(sessao):
    repositorio = RepositorioLancamento(sessao, _preparar(sessao))

    assert repositorio.listar() == []
