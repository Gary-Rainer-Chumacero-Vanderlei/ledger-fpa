from io import BytesIO

from ofxtools.Parser import OFXTree

OFX_MINIMO = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<BANKMSGSRSV1><STMTTRNRS><STMTRS>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20171231220000[-3:BRT]
<TRNAMT>-83.93
<FITID>20171231001
<MEMO>COMPRA COM CARTÃO
</STMTTRN>
</BANKTRANLIST>
</STMTRS></STMTTRNRS></BANKMSGSRSV1>
</OFX>
""".encode("cp1252")


def test_ofxtools_le_um_ofx_minimo():
    arvore = OFXTree()
    arvore.parse(BytesIO(OFX_MINIMO))

    transacao = arvore.getroot().find(".//STMTTRN")

    assert transacao is not None
    assert transacao.findtext("TRNAMT") == "-83.93"
    assert transacao.findtext("DTPOSTED") == "20171231220000[-3:BRT]"
    assert transacao.findtext("MEMO") == "COMPRA COM CARTÃO"
