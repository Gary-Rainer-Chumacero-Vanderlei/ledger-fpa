from datetime import date
from decimal import Decimal

import pytest
from ledger_fpa.infra.leitor_ofx import ArquivoOfxInvalido, ler_extrato

from ledger_fpa.domain.transacao_extrato import Sentido, TransacaoExtrato

CABECALHO = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

"""

CABECALHO_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<?OFX OFXHEADER="200" VERSION="211" SECURITY="NONE" '
    'OLDFILEUID="NONE" NEWFILEUID="NONE"?>\n'
)

OFX_XML = (
    CABECALHO_XML
    + """<OFX>
<BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20171231220000[-3:BRT]</DTPOSTED>
<TRNAMT>-52.30</TRNAMT>
<FITID>X1</FITID>
<MEMO>COMPRA COM CARTÃO</MEMO>
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT</TRNTYPE>
<DTPOSTED>20180102000000[-3:BRT]</DTPOSTED>
<TRNAMT>139.75</TRNAMT>
<FITID>X2</FITID>
<MEMO>BB CURTO PRAZO</MEMO>
</STMTTRN>
</BANKTRANLIST>
</STMTRS></STMTTRNRS></BANKMSGSRSV1>
</OFX>
"""
)


def _trn(
    *,
    dtposted="20171202000000[-3:BRT]",
    trnamt="-83.93",
    fitid="20171202001",
    memo="COMPRA COM CARTÃO",
    name=None,
    checknum=None,
    refnum=None,
):
    campos = [
        ("TRNTYPE", "OTHER"),
        ("DTPOSTED", dtposted),
        ("TRNAMT", trnamt),
        ("FITID", fitid),
        ("CHECKNUM", checknum),
        ("REFNUM", refnum),
        ("NAME", name),
        ("MEMO", memo),
    ]
    linhas = [f"<{tag}>{valor}" for tag, valor in campos if valor is not None]
    return "<STMTTRN>\n" + "\n".join(linhas) + "\n</STMTTRN>"


def _extrato(*transacoes):
    return (
        "<STMTTRNRS>\n<STMTRS>\n<CURDEF>BRL\n"
        "<BANKACCTFROM>\n<BANKID>001\n<ACCTID>56789-0\n<ACCTTYPE>CHECKING\n"
        "</BANKACCTFROM>\n<BANKTRANLIST>\n"
        + "\n".join(transacoes)
        + "\n</BANKTRANLIST>\n</STMTRS>\n</STMTTRNRS>"
    )


def _ofx(*extratos):
    corpo = (
        "<OFX>\n<BANKMSGSRSV1>\n" + "\n".join(extratos) + "\n</BANKMSGSRSV1>\n</OFX>\n"
    )
    return (CABECALHO + corpo).encode("cp1252")


def _ler(tmp_path, *transacoes):
    caminho = tmp_path / "extrato.ofx"
    caminho.write_bytes(_ofx(_extrato(*transacoes)))
    return ler_extrato(caminho)


def test_le_uma_saida_como_subtrai(tmp_path):
    transacoes = _ler(tmp_path, _trn())

    assert transacoes == [
        TransacaoExtrato(
            data=date(2017, 12, 2),
            historico="COMPRA COM CARTÃO",
            valor=Decimal("83.93"),
            sentido=Sentido.SUBTRAI,
            identificador="20171202001",
        )
    ]


def test_le_uma_entrada_como_soma(tmp_path):
    transacoes = _ler(tmp_path, _trn(trnamt="11760.00", fitid="2"))

    assert transacoes[0].sentido is Sentido.SOMA
    assert transacoes[0].valor == Decimal("11760.00")


def test_preserva_os_acentos_do_windows_1252(tmp_path):
    transacoes = _ler(tmp_path, _trn(memo="TARIFA PACOTE DE SERVIÇOS"))

    assert transacoes[0].historico == "TARIFA PACOTE DE SERVIÇOS"


@pytest.mark.parametrize(
    ("dtposted", "esperada"),
    [
        ("20171231220000[-3:BRT]", date(2017, 12, 31)),
        ("20171231235500[-3:BRT]", date(2017, 12, 31)),
        ("20180101000000[-3:BRT]", date(2018, 1, 1)),
        ("20171202", date(2017, 12, 2)),
        ("20171231220000", date(2017, 12, 31)),
    ],
)
def test_a_data_e_a_que_o_banco_escreveu(tmp_path, dtposted, esperada):
    transacoes = _ler(tmp_path, _trn(dtposted=dtposted))

    assert transacoes[0].data == esperada


@pytest.mark.parametrize(
    ("trnamt", "esperado", "sentido"),
    [
        ("-83,93", Decimal("83.93"), Sentido.SUBTRAI),
        ("-36", Decimal("36"), Sentido.SUBTRAI),
        ("+5.00", Decimal("5.00"), Sentido.SOMA),
        ("139,75", Decimal("139.75"), Sentido.SOMA),
    ],
)
def test_le_o_valor_em_formatos_aceitos(tmp_path, trnamt, esperado, sentido):
    transacao = _ler(tmp_path, _trn(trnamt=trnamt))[0]

    assert transacao.valor == esperado
    assert transacao.sentido is sentido


@pytest.mark.parametrize("trnamt", ["1.234,56", "1,234.56", "ABC", "1e3", "NaN", ""])
def test_rejeita_valor_invalido(tmp_path, trnamt):
    with pytest.raises(ArquivoOfxInvalido):
        _ler(tmp_path, _trn(trnamt=trnamt))


def test_rejeita_valor_com_mais_de_duas_casas(tmp_path):
    with pytest.raises(ArquivoOfxInvalido):
        _ler(tmp_path, _trn(trnamt="-10.123"))


def test_ignora_transacao_de_valor_zero(tmp_path):
    transacoes = _ler(
        tmp_path,
        _trn(trnamt="0.00", fitid="1"),
        _trn(trnamt="-5.00", fitid="2"),
    )

    assert [t.identificador for t in transacoes] == ["2"]


def test_historico_vem_do_memo_ou_do_name(tmp_path):
    transacoes = _ler(
        tmp_path,
        _trn(memo="DO MEMO", name="DO NAME", fitid="1"),
        _trn(memo=None, name="DO NAME", fitid="2"),
    )

    assert [t.historico for t in transacoes] == ["DO MEMO", "DO NAME"]


def test_rejeita_transacao_sem_historico(tmp_path):
    with pytest.raises(ArquivoOfxInvalido):
        _ler(tmp_path, _trn(memo=None, name=None))


@pytest.mark.parametrize(
    ("checknum", "refnum", "esperado"),
    [("180880", "999", "180880"), (None, "999", "999"), (None, None, None)],
)
def test_documento_vem_do_checknum_ou_do_refnum(tmp_path, checknum, refnum, esperado):
    transacao = _ler(tmp_path, _trn(checknum=checknum, refnum=refnum))[0]

    assert transacao.documento == esperado


@pytest.mark.parametrize("campo", ["dtposted", "trnamt", "fitid"])
def test_rejeita_transacao_sem_campo_obrigatorio(tmp_path, campo):
    with pytest.raises(ArquivoOfxInvalido):
        _ler(tmp_path, _trn(**{campo: None}))


@pytest.mark.parametrize("dtposted", ["20171340000000", "ABCDEFGH", "2017", "2017111"])
def test_rejeita_data_invalida(tmp_path, dtposted):
    with pytest.raises(ArquivoOfxInvalido):
        _ler(tmp_path, _trn(dtposted=dtposted))


def test_preserva_a_ordem_do_arquivo(tmp_path):
    transacoes = _ler(
        tmp_path,
        _trn(fitid="3"),
        _trn(fitid="1"),
        _trn(fitid="2"),
    )

    assert [t.identificador for t in transacoes] == ["3", "1", "2"]


def test_extrato_sem_transacoes_devolve_lista_vazia(tmp_path):
    assert _ler(tmp_path) == []


def test_aceita_extrato_sem_saldo(tmp_path):
    assert len(_ler(tmp_path, _trn())) == 1


def test_rejeita_arquivo_com_mais_de_um_extrato(tmp_path):
    caminho = tmp_path / "extrato.ofx"
    caminho.write_bytes(_ofx(_extrato(_trn()), _extrato(_trn(fitid="2"))))

    with pytest.raises(ArquivoOfxInvalido):
        ler_extrato(caminho)


def test_rejeita_arquivo_sem_extrato(tmp_path):
    caminho = tmp_path / "extrato.ofx"
    caminho.write_bytes(_ofx())

    with pytest.raises(ArquivoOfxInvalido):
        ler_extrato(caminho)


@pytest.mark.parametrize(
    "conteudo",
    [b"", "isto não é um OFX".encode("cp1252"), bytes(range(256))],
)
def test_rejeita_arquivo_que_nao_e_ofx(tmp_path, conteudo):
    caminho = tmp_path / "extrato.ofx"
    caminho.write_bytes(conteudo)

    with pytest.raises(ArquivoOfxInvalido):
        ler_extrato(caminho)


def test_arquivo_inexistente_levanta_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        ler_extrato(tmp_path / "nao_existe.ofx")


def test_aceita_caminho_como_texto_e_como_path(tmp_path):
    caminho = tmp_path / "extrato.ofx"
    caminho.write_bytes(_ofx(_extrato(_trn())))

    assert ler_extrato(str(caminho)) == ler_extrato(caminho)


def test_aceita_arquivo_aberto_em_modo_binario(tmp_path):
    caminho = tmp_path / "extrato.ofx"
    caminho.write_bytes(_ofx(_extrato(_trn())))

    with caminho.open("rb") as arquivo:
        transacoes = ler_extrato(arquivo)

    assert len(transacoes) == 1


def test_le_ofx_2x_em_xml(tmp_path):
    caminho = tmp_path / "extrato.ofx"
    caminho.write_bytes(OFX_XML.encode("utf-8"))

    transacoes = ler_extrato(caminho)

    assert [(t.data, t.valor, t.sentido) for t in transacoes] == [
        (date(2017, 12, 31), Decimal("52.30"), Sentido.SUBTRAI),
        (date(2018, 1, 2), Decimal("139.75"), Sentido.SOMA),
    ]
